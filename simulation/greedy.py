import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import List

from simulation.classes import Lot, Machine
from simulation.dispatching.dispatcher import dispatcher_map
from simulation.file_instance import FileInstance
from simulation.plugins.cost_plugin import CostPlugin
from simulation.randomizer import Randomizer
from simulation.read import read_all
from simulation.stats import print_statistics

import argparse

last_sort_time = -1


def dispatching_combined_permachine(ptuple_fcn, machine, time, setups):
    for lot in machine.waiting_lots:
        lot.ptuple = ptuple_fcn(lot, time, machine, setups)


def get_lots_to_dispatch_by_machine(instance, ptuple_fcn, machine=None):
    """머신 기준으로 디스패칭할 로트 선택 (L4M 방식)"""
    time = instance.current_time
    if machine is None:
        for machine in instance.usable_machines:
            break
    # 대기 중인 모든 로트의 우선순위 튜플(ptuple) 계산
    dispatching_combined_permachine(ptuple_fcn, machine, time, instance.setups)
    # ptuple 기준으로 정렬 (작은 값 = 높은 우선순위)
    wl = sorted(machine.waiting_lots, key=lambda k: k.ptuple)
    # 가장 높은 우선순위 로트 선택
    lot = wl[0]

    # ========== 배치 처리 로직 ==========
    if lot.actual_step.batch_max > 1:
        # 같은 step_name끼리 그룹핑 (배치로 묶을 수 있는 로트들)
        lot_m = defaultdict(lambda: [])
        for w in wl:
            lot_m[w.actual_step.step_name].append(w)
        # 그룹별 우선순위 정렬
        lot_l = sorted(list(lot_m.values()),
                       key=lambda l: (
                           l[0].ptuple[0],  # CQT 대기 중인 로트 우선
                           l[0].ptuple[1],  # min_runs 제약 준수 우선
                           -min(1, len(l) / l[0].actual_step.batch_max),  # 배치 채움률 높은 것 우선 (음수라서 큰 값이 앞으로)
                           0 if len(l) >= l[0].actual_step.batch_min else 1,  # batch_min 충족하는 것 우선
                           *(l[0].ptuple[2:]),  # 나머지는 기본 우선순위 규칙 따름
                       ))
        lots: List[Lot] = lot_l[0]  # 가장 우선순위 높은 그룹 선택
        # batch_max 초과 시 잘라냄
        if len(lots) > lots[0].actual_step.batch_max:
            lots = lots[:lots[0].actual_step.batch_max]
        # batch_min 미만이면 처리 안함 (더 모일 때까지 대기)
        if len(lots) < lots[0].actual_step.batch_min:
            lots = None
    else:
        # ========== 단일 로트 처리 ==========
        lots = [lot]

    # ========== Setup 최적화 ==========
    # 현재 머신의 setup과 로트의 setup이 다르면, 같은 setup을 가진 다른 머신 찾기
    if lots is not None and machine.current_setup != lots[0].actual_step.setup_needed:
        m: Machine
        for m in instance.family_machines[machine.family]:
            if m in instance.usable_machines and m.current_setup == lots[0].actual_step.setup_needed:
                machine = m  # setup 변경 없이 처리 가능한 머신으로 교체
                break

    # ========== min_runs 제약 처리 ==========
    # min_runs_left가 남아있는데 다른 setup 로트를 처리하려 하면 거부 (최대 5회까지)
    if machine.dispatch_failed < 5 and machine.min_runs_left is not None and machine.min_runs_setup != lots[0].actual_step.setup_needed:
        machine.dispatch_failed += 1
        lots = None  # 디스패칭 실패 처리
    if lots is not None:
        machine.dispatch_failed = 0
    return machine, lots


def build_batch(lot, nexts):
    """같은 step_name을 가진 로트들을 배치로 묶음"""
    batch = [lot]
    if lot.actual_step.batch_max > 1:
        for bo_lot in nexts:
            # 같은 공정 단계인 로트만 배치에 추가
            if lot.actual_step.step_name == bo_lot.actual_step.step_name:
                batch.append(bo_lot)
            # batch_max에 도달하면 중단
            if len(batch) == lot.actual_step.batch_max:
                break
    return batch


def get_lots_to_dispatch_by_lot(instance, current_time, dispatcher):
    global last_sort_time
    if last_sort_time != current_time:
        for lot in instance.usable_lots:
            lot.ptuple = dispatcher(lot, current_time, None)
        last_sort_time = current_time
        instance.usable_lots.sort(key=lambda k: k.ptuple)
    lots = instance.usable_lots
    setup_machine, setup_batch = None, None
    min_run_break_machine, min_run_break_batch = None, None
    family_lock = None
    for i in range(len(lots)):
        lot: Lot = lots[i]
        if family_lock is None or family_lock == lot.actual_step.family:
            family_lock = lot.actual_step.family
            assert len(lot.waiting_machines) > 0
            for machine in lot.waiting_machines:
                if lot.actual_step.setup_needed == '' or lot.actual_step.setup_needed == machine.current_setup:
                    return machine, build_batch(lot, lots[i + 1:])
                else:
                    if setup_machine is None and machine.min_runs_left is None:
                        setup_machine = machine
                        setup_batch = i
                    if min_run_break_machine is None:
                        min_run_break_machine = machine
                        min_run_break_batch = i
    if setup_machine is not None:
        return setup_machine, build_batch(lots[setup_batch], lots[setup_batch + 1:])
    return min_run_break_machine, build_batch(lots[min_run_break_batch], lots[min_run_break_batch + 1:])


def run_greedy():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=str)
    p.add_argument('--days', type=int)
    p.add_argument('--dispatcher', type=str)
    p.add_argument('--seed', type=int)
    p.add_argument('--wandb', action='store_true', default=False)
    p.add_argument('--chart', action='store_true', default=False)
    p.add_argument('--alg', type=str, default='l4m', choices=['l4m', 'm4l'])
    a = p.parse_args()

    sys.stderr.write('Loading ' + a.dataset + ' for ' + str(a.days) + ' days, using ' + a.dispatcher + '\n')
    sys.stderr.flush()

    start_time = datetime.now()

    files = read_all('datasets/' + a.dataset)

    run_to = 3600 * 24 * a.days
    Randomizer().random.seed(a.seed)
    l4m = a.alg == 'l4m'
    plugins = []
    if a.wandb:
        from simulation.plugins.wandb_plugin import WandBPlugin
        plugins.append(WandBPlugin())
    if a.chart:
        from simulation.plugins.chart_plugin import ChartPlugin
        plugins.append(ChartPlugin())
    plugins.append(CostPlugin())
    instance = FileInstance(files, run_to, l4m, plugins)

    dispatcher = dispatcher_map[a.dispatcher]

    sys.stderr.write('Starting simulation with dispatching rule\n\n')
    sys.stderr.flush()

    while not instance.done:
        done = instance.next_decision_point()
        instance.print_progress_in_days()
        if done or instance.current_time > run_to:
            break

        if l4m:
            machine, lots = get_lots_to_dispatch_by_machine(instance, dispatcher)
            if lots is None:
                instance.usable_machines.remove(machine)
            else:
                instance.dispatch(machine, lots)
        else:
            machine, lots = get_lots_to_dispatch_by_lot(instance, instance.current_time, dispatcher)
            if lots is None:
                instance.usable_lots.clear()
                instance.lot_in_usable.clear()
                instance.next_step()
            else:
                instance.dispatch(machine, lots)

    instance.finalize()
    interval = datetime.now() - start_time
    print(instance.current_time_days, ' days simulated in ', interval)
    print_statistics(instance, a.days, a.dataset, a.dispatcher, method='greedy_seed' + str(a.seed))
