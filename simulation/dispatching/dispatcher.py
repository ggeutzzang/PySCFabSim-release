from simulation.classes import Lot, Machine
from simulation.randomizer import Randomizer

r = Randomizer()


class Dispatchers:
    """디스패칭 전략 클래스 - 로트의 우선순위 튜플(ptuple)을 계산"""

    @staticmethod
    def get_setup(new_setup, machine, actual_step_setup_time, setups):
        """setup 변경에 필요한 시간 계산

        - setup 변경이 필요 없으면 0 반환
        - Step에 setup_time이 있으면 그 값 사용
        - 없으면 setups 딕셔너리에서 (현재setup, 새setup) 조회
        """
        if new_setup != '' and machine.current_setup != new_setup:
            if actual_step_setup_time is not None:
                return actual_step_setup_time
            elif (machine.current_setup, new_setup) in setups:
                return setups[(machine.current_setup, new_setup)]
            elif ('', new_setup) in setups:
                return setups[('', new_setup)]
        return 0

    @staticmethod
    def fifo_ptuple_for_lot(lot: Lot, time, machine: Machine = None, setups=None):
        """FIFO: 먼저 도착한 로트 우선

        ptuple 구조 (작은 값이 높은 우선순위):
        (min_runs 준수, CQT 대기, setup 시간, 우선순위, 도착시간, 마감시간)
        """
        if machine is not None:
            lot.ptuple = (
                # min_runs 제약: 0=준수, 1=위반
                0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
                # CQT 대기: 0=CQT 대기중(우선), 1=일반
                0 if lot.cqt_waiting is not None else 1,
                # setup 변경 시간 (짧을수록 우선)
                Dispatchers.get_setup(lot.actual_step.setup_needed, machine, lot.actual_step.setup_time, setups),
                # 로트 우선순위 (음수이므로 높을수록 앞으로)
                -lot.priority,
                # 도착 시간 (FIFO - 먼저 온 것이 작은 값)
                lot.free_since,
                # 마감 시간 (보조 기준)
                lot.deadline_at,
            )
            return lot.ptuple
        else:
            # M4L 모드: 머신 정보 없이 호출
            return -lot.priority, lot.free_since, lot.deadline_at,

    @staticmethod
    def cr_ptuple_for_lot(lot: Lot, time, machine: Machine = None, setups=None):
        """CR: 긴급한 로트 우선 (Critical Ratio 낮을수록 긴급)

        FIFO와 동일하지만 마지막에 free_since 대신 cr(time) 사용
        CR = (마감까지 남은 시간) / (남은 작업 시간)
        """
        if machine is not None:
            lot.ptuple = (
                0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
                0 if lot.cqt_waiting is not None else 1,
                Dispatchers.get_setup(lot.actual_step.setup_needed, machine, lot.actual_step.setup_time, setups),
                -lot.priority,
                # Critical Ratio (FIFO의 free_since 대신)
                lot.cr(time),
            )
            return lot.ptuple
        else:
            return -lot.priority, lot.cr(time),

    @staticmethod
    def random_ptuple_for_lot(lot: Lot, time, machine: Machine = None, setups=None):
        """Random: 무작위 선택 (벤치마크/비교용)

        min_runs와 CQT 제약은 준수하고, 나머지는 랜덤
        """
        if machine is not None:
            return (
                0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
                0 if lot.cqt_waiting is not None else 1,
                r.random.uniform(0, 99999),  # 랜덤 값
            )
        else:
            return r.random.uniform(0, 99999),


# 디스패처 이름 → 함수 매핑
dispatcher_map = {
    'fifo': Dispatchers.fifo_ptuple_for_lot,
    'cr': Dispatchers.cr_ptuple_for_lot,
    'random': Dispatchers.random_ptuple_for_lot,
}
