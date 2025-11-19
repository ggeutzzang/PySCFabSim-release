# PySCFabSim 학습 계획

> 반도체 제조 시뮬레이터 및 강화학습 기반 디스패칭 최적화 프로젝트
>
> 프로젝트 경로: `/home/iamhjoo/project/PySCFabSim-release`

## 📋 목차

- [[#1단계 기초 개념 이해 (1-2일)]]
- [[#2단계 데이터 흐름 추적 (2-3일)]]
- [[#3단계 디스패칭 시스템 심화 (3-4일)]]
- [[#4단계 제약사항 및 최적화 (3-4일)]]
- [[#5단계 강화학습 환경 이해 (4-5일)]]
- [[#6단계 RL 학습 실습 (5-7일)]]
- [[#7단계 결과 분석 및 최적화 (3-4일)]]
- [[#8단계 커스터마이징 및 확장 (선택사항)]]

---

## 📚 1단계: 기초 개념 이해 (1-2일)

### 1.1 반도체 제조 기본 개념

- [ ] **Lot**: 제조 단위 (웨이퍼 묶음)
- [ ] **Machine/Station**: 제조 장비
- [ ] **Route**: 제품의 제조 경로
- [ ] **Step**: 개별 공정 단계
- [ ] **Setup**: 장비 설정 변경
- [ ] **Dispatching**: 로트-머신 할당 결정

### 1.2 시뮬레이션 기본 개념

- [ ] 이벤트 기반 시뮬레이션 (Discrete Event Simulation)
- [ ] Priority queue와 이벤트 스케줄링
- [ ] 시뮬레이션 시간 vs 실제 시간

### 실습

```bash
# 프로젝트 디렉토리로 이동
cd /home/iamhjoo/project/PySCFabSim-release
```

**파일 읽기:**
- [ ] `simulation/classes.py` - 주요 클래스 속성 파악
- [ ] `datasets/SMT2020_HVLM/` - 데이터셋 파일 구조 확인
  - `tool.txt.1l`: 머신 정보
  - `order.txt`: 주문 정보
  - `route_*.txt`: 제조 경로

**학습 노트:**
```
- Lot의 생명주기: release → 각 Step 처리 → done
- Machine의 상태: idle → processing → idle
- 이벤트 종류: MachineDone, LotDone, Breakdown, Release
```

---

## 🔍 2단계: 데이터 흐름 추적 (2-3일)

### 2.1 초기화 과정 따라가기

**파일 순서:**
1. [ ] `main.py` - 시작점 확인
2. [ ] `simulation/read.py`의 `read_all()` - 데이터셋 로딩
3. [ ] `simulation/file_instance.py`의 `__init__()` - 객체 생성
4. [ ] `simulation/instance.py`의 `Instance` 클래스

### 실습

```bash
# 간단한 FIFO 실험 실행 (짧은 기간)
pypy3 main.py --days 30 --dataset HVLM --dispatcher fifo --seed 0 --alg l4m
```

**관찰 사항:**
- [ ] 실행 중 출력 관찰 (시뮬레이션 진행 상황)
- [ ] 생성된 JSON 결과 파일 분석 (`greedy/` 디렉토리)
- [ ] ACT, throughput, on_time% 지표 확인

### 2.2 이벤트 흐름 이해

**핵심 파일:**
1. [ ] `simulation/event_queue.py` - 이벤트 큐 구조
2. [ ] `simulation/events.py` - 4가지 이벤트 타입
3. [ ] `instance.py`의 `next_step()` - 시간 진행 로직

**실습:**
- [ ] 디버거 사용 또는 print 문 추가하여 이벤트 순서 추적
- [ ] MachineDoneEvent → free_up_machines → dispatch 흐름 확인

**이벤트 플로우 다이어그램:**
```
ReleaseEvent
    ↓
로트가 active_lots에 추가
    ↓
free_up_lots() 호출
    ↓
머신에 대기 로트 등록
    ↓
dispatch() 호출
    ↓
MachineDoneEvent, LotDoneEvent 생성
    ↓
이벤트 큐에 삽입
    ↓
next_step()에서 이벤트 처리
```

---

## ⚙️ 3단계: 디스패칭 시스템 심화 (3-4일)

### 3.1 Priority Tuple 시스템

**핵심 파일:**
- [ ] `simulation/dispatching/dispatcher.py` - FIFO, CR, Random 전략

**Priority Tuple 구조 이해:**

```python
# FIFO ptuple
(
    min_runs_violation,  # 0 또는 1
    cqt_waiting,         # 0 또는 1
    setup_time,          # 시간 (초)
    -priority,           # 음수 (높은 우선순위가 먼저)
    free_since,          # 대기 시작 시간
    deadline_at,         # 마감일
)

# CR ptuple
(
    min_runs_violation,
    cqt_waiting,
    setup_time,
    -priority,
    cr(time),            # Critical Ratio (작을수록 긴급)
)
```

### 실습

```bash
# 동일 조건에서 dispatcher만 변경하여 비교
pypy3 main.py --days 90 --dataset HVLM --dispatcher fifo --seed 42 --alg l4m
pypy3 main.py --days 90 --dataset HVLM --dispatcher cr --seed 42 --alg l4m

# 결과 비교
python3 eval_results.py
```

**분석 포인트:**
- [ ] FIFO vs CR의 ACT 차이
- [ ] on_time% 비교
- [ ] tardiness 비교

### 3.2 L4M vs M4L 모드

**Lot-for-Machine (L4M):**
- [ ] `simulation/dispatching/dm_lot_for_machine.py` 분석
- 머신이 유휴 상태가 되면 → 최적의 로트 선택
- RL 환경에서 주로 사용

**Machine-for-Lot (M4L):**
- [ ] `simulation/dispatching/dm_machine_for_lot.py` 분석
- 로트가 준비되면 → 최적의 머신 선택
- Greedy 알고리즘 변형

**실습:**
- [ ] `simulation/greedy.py`의 두 가지 전략 비교
  - `get_lots_to_dispatch_by_machine()` (25-66행)
  - `get_lots_to_dispatch_by_lot()` (80-108행)

---

## 🎯 4단계: 제약사항 및 최적화 (3-4일)

### 4.1 배치 처리 (Batching)

**개념:**
- 일부 공정은 여러 로트를 한 번에 처리 (배치)
- `batch_min` ~ `batch_max` 범위 내에서 배치 크기 결정

**핵심 코드:**
- [ ] `classes.py`의 `Step.batch_min/batch_max` (115-117행)
- [ ] `greedy.py`의 배치 그룹화 로직 (34-51행)
- [ ] `instance.py`의 dispatch에서 배치 처리

**실습:**
```python
# Step 클래스에서 배치 속성 확인
self.batching = d['PTPER'] == 'per_batch'
self.batch_min = 1 if d['BATCHMN'] == '' else int(d['BATCHMN'] / pieces_per_lot)
self.batch_max = 1 if d['BATCHMX'] == '' else int(d['BATCHMX'] / pieces_per_lot)
```

### 4.2 Setup 최적화

**개념:**
- Setup 변경 시 setup_time 소요
- `min_runs`: 동일 setup을 최소 N번 실행해야 하는 제약

**핵심 코드:**
- [ ] Setup time 계산 (`instance.py` 186-196행)
- [ ] Min runs 제약 (`instance.py` 152-156행, 197-200행)
- [ ] Setup 위반 패널티 (RL에서 -10)

**Setup 전환 로직:**
```python
new_setup = lots[0].actual_step.setup_needed
if new_setup != '' and machine.current_setup != new_setup:
    setup_time = setups.get((machine.current_setup, new_setup), 0)

    if new_setup in self.setup_min_run:
        machine.min_runs_left = self.setup_min_run[new_setup]
        machine.min_runs_setup = new_setup
```

### 4.3 고급 제약사항

**CQT (Critical Queue Time):**
- [ ] 특정 스텝 완료 후 다음 특정 스텝까지 최대 대기 시간 제약
- [ ] Priority tuple에서 최우선으로 처리
- [ ] `classes.py` 121-122행

**Cascading:**
- [ ] 파이프라인 방식 처리 (첫 부품 처리 후 다음 로트 시작 가능)
- [ ] `instance.py` 170-184행

**Dedication (Lot-to-Lens):**
- [ ] 특정 로트가 특정 머신에 고정 할당
- [ ] `instance.py` 148-150행

**Breakdown & PM:**
- [ ] 장비 고장 및 예방 정비
- [ ] `events.py`의 `BreakdownEvent` (44-76행)

### 실습: 제약 제거 실험

```bash
# 환경변수로 제약 제거
export NOWIP=1        # WIP 제거
export NOBREAKDOWN=1  # Breakdown 제거
export NOPM=1         # PM 제거
export NOREWORK=1     # Rework 제거

pypy3 main.py --days 90 --dataset HVLM --dispatcher fifo --seed 0 --alg l4m

# 환경변수 해제
unset NOWIP NOBREAKDOWN NOPM NOREWORK
```

**분석:**
- [ ] 제약 제거 전후 throughput 비교
- [ ] 시뮬레이션 속도 차이

---

## 🤖 5단계: 강화학습 환경 이해 (4-5일)

### 5.1 RL 환경 구조

**핵심 파일:**
- [ ] `simulation/gym/environment.py` - `DynamicSCFabSimulationEnvironment`

**OpenAI Gym 인터페이스:**
```python
class DynamicSCFabSimulationEnvironment(Env):
    def reset(self):
        # 환경 초기화, 초기 상태 반환

    def step(self, action):
        # 액션 실행, (state, reward, done, info) 반환

    @property
    def observation_space(self):
        # 상태 공간 정의

    @property
    def action_space(self):
        # 액션 공간 정의 (Discrete(num_actions))
```

### 5.2 상태 공간 설계

**구조:**
```
상태 벡터 = [머신 특징(4개)] + [액션1 특징(6개)] + [액션2 특징(6개)] + ... + [액션N 특징(6개)]
```

**머신 레벨 특징 (4개):**
1. 다음 PM까지 시간
2. Setup/Processing 비율
3. 비유휴 시간 비율
4. 머신 클래스

**액션(로트 그룹)별 특징 (DEMO_ENV_1 기준 6개):**
1. `NO_LOTS_PER_BATCH`: 배치 크기 / batch_max
2. `CR.MAX`: 그룹 내 최대 CR
3. `FREE_SINCE.MAX`: 그룹 내 최대 대기 시간
4. `SETUP.MIN_RUNS_OK`: min_runs 준수 여부
5. `SETUP.NEEDED`: setup 필요 여부
6. `SETUP.LAST_SETUP_TIME`: 마지막 setup 시간

**핵심 파일:**
- [ ] `simulation/gym/E.py` - 상태 컴포넌트 열거
- [ ] `simulation/gym/sample_envs.py` - DEMO_ENV_1

### 5.3 보상 함수 분석

**Reward Type 1: 완료 + Tardiness 패널티**
```python
reward += 1000  # 로트 완료 시
if lot.deadline_at >= lot.done_at:
    reward += 1000  # 기한 내 완료
else:
    reward -= min(500, (lot.done_at - lot.deadline_at) / 3600)  # 지연 패널티
```

**Reward Type 2: 완료 + On-time 보너스**
```python
reward += 1000  # 로트 완료 시
reward += 1000 if lot.deadline_at >= lot.done_at else 0  # on-time 여부만
```

**Reward Type 3: 평균 CR 기반**
```python
reward += mean([min(1, lot.cr(current_time) - 1) for lot in active_lots])
# CR < 1이면 음수 보상 (긴급)
```

**Reward Type 7: 평균 Not-lateness 기반**
```python
reward += mean([lot.notlateness(current_time) for lot in active_lots])
```

**공통 패널티:**
```python
if violated_minruns:
    reward -= 10  # min_runs 위반 시
```

### 실습: 환경 테스트

```python
cd /home/iamhjoo/project/PySCFabSim-release

# Python 인터프리터 실행
python3
```

```python
from simulation.gym.environment import DynamicSCFabSimulationEnvironment
from simulation.gym.sample_envs import DEMO_ENV_1

# 환경 생성
env = DynamicSCFabSimulationEnvironment(
    **DEMO_ENV_1,
    num_actions=9,
    active_station_group=None,
    days=30,
    dataset='SMT2020_HVLM',
    dispatcher='fifo',
    seed=0,
    max_steps=10000,
    reward_type=2
)

# 환경 초기화
state = env.reset()
print(f"State shape: {len(state)}")
print(f"State: {state[:10]}...")  # 처음 10개만 출력
print(f"Action space: {env.action_space}")

# 랜덤 에이전트 테스트
total_reward = 0
for step in range(100):
    action = env.action_space.sample()
    state, reward, done, info = env.step(action)
    total_reward += reward
    print(f"Step {step}: Action={action}, Reward={reward:.2f}, Done={done}")
    if done:
        break

print(f"Total reward: {total_reward}")
```

**체크리스트:**
- [ ] 환경 생성 성공
- [ ] state 벡터 크기 확인 (4 + 9×6 = 58)
- [ ] 랜덤 액션 실행 성공
- [ ] 보상 변화 관찰

---

## 🚀 6단계: RL 학습 실습 (5-7일)

### 6.1 실험 설정 생성

**핵심 파일:**
- [ ] `exp_set_gen.py` - 실험 config 생성 스크립트

**Config JSON 구조:**
```json
{
  "name": "experiment_name",
  "params": {
    "seed": 0,
    "dataset": "HVLM",
    "action_count": 9,
    "training_period": 730,
    "dispatcher": "fifo",
    "reward": 2,
    "station_group": "<Implant_128>"
  }
}
```

**실습:**
```bash
# exp_set_gen.py 수정 (작은 실험 생성)
python3 exp_set_gen.py

# 생성된 실험 확인
ls experiments/
cat experiments/test_exp/config.json
```

### 6.2 RL 학습 실행

**핵심 파일:**
- [ ] `rl_train.py` - PPO 학습 스크립트

**학습 파라미터:**
- `total_timesteps`: 1,000,000 (약 수 시간)
- `checkpoint_freq`: 100,000 (10개 체크포인트)
- `algorithm`: PPO (Proximal Policy Optimization)

**실습: 짧은 학습**
```bash
# 테스트용 짧은 학습 (100k 스텝, ~1시간)
# 먼저 rl_train.py의 to_train을 100000으로 수정

python3 rl_train.py experiments/test_exp/config.json
```

**모니터링:**
- [ ] 학습 진행 상황 출력 확인
- [ ] 체크포인트 저장 확인 (`experiments/test_exp/checkpoint_*.zip`)
- [ ] 최종 모델 저장 확인 (`trained.weights.zip`)

**학습 로그 분석:**
```
ep_len_mean: 평균 에피소드 길이
ep_rew_mean: 평균 에피소드 보상
fps: 초당 프레임 수
time_elapsed: 경과 시간
```

### 6.3 RL 평가

**핵심 파일:**
- [ ] `rl_test.py` - 체크포인트 평가
- [ ] `test_rl_agents.py` - 자동 평가 스크립트

**평가 방법:**
```bash
# 특정 체크포인트 평가
python3 rl_test.py experiments/test_exp trained.weights

# 랜덤 에이전트와 비교
python3 rl_test.py experiments/test_exp random

# Greedy 전략과 비교
python3 rl_test.py experiments/test_exp greedy

# 모든 체크포인트 자동 평가
python3 test_rl_agents.py
```

**평가 결과 분석:**
- [ ] 180일 체크포인트 통계
- [ ] 365일 체크포인트 통계
- [ ] RL vs Greedy vs Random 비교

**성능 지표:**
- ACT (Average Cycle Time)
- Throughput (완료된 로트 수)
- On-time % (기한 내 완료율)
- Tardiness (평균 지연 시간)

---

## 📊 7단계: 결과 분석 및 최적화 (3-4일)

### 7.1 통계 분석

**핵심 파일:**
- [ ] `simulation/stats.py` - 지표 계산
- [ ] `eval_results.py` - 결과 집계

**실습:**
```bash
# 여러 실험 결과 비교
python3 eval_results.py

# 출력 파일 확인
cat greedy/_greedy_sum.txt
```

**출력 예시:**
```
Lot Statistics:
  ACT: 45.2 days
  Throughput: 1234 lots
  On-time: 87%
  Tardiness: 2.3 days

Machine Statistics:
  Availability: 92%
  Utilization: 78%
  Setup time: 5%
  PM time: 3%
  Breakdown time: 5%
```

### 7.2 성능 비교 매트릭스

| 전략 | ACT (days) | Throughput | On-time % | Tardiness (days) |
|------|------------|------------|-----------|------------------|
| FIFO | ? | ? | ? | ? |
| CR | ? | ? | ? | ? |
| Random | ? | ? | ? | ? |
| RL (Type 1) | ? | ? | ? | ? |
| RL (Type 2) | ? | ? | ? | ? |

**실습:**
- [ ] 위 표를 채우기 위한 실험 실행
- [ ] 각 전략별 3개 시드로 실험 (seed 0, 42, 123)
- [ ] 평균 및 표준편차 계산

### 7.3 데이터셋 비교

**HVLM vs LVHM:**
```bash
# HVLM (High Volume Low Mix)
pypy3 main.py --days 180 --dataset HVLM --dispatcher cr --seed 0 --alg l4m

# LVHM (Low Volume High Mix)
pypy3 main.py --days 180 --dataset LVHM --dispatcher cr --seed 0 --alg l4m
```

**분석 포인트:**
- [ ] HVLM: 높은 throughput, 낮은 복잡도
- [ ] LVHM: 낮은 throughput, 높은 setup 빈도

### 7.4 하이퍼파라미터 튜닝

**실험 변수:**

1. **num_actions** (액션 공간 크기)
   - [ ] 5, 9, 15, 20으로 실험
   - 가설: 너무 작으면 표현력 부족, 너무 크면 학습 어려움

2. **state_components** (상태 특징)
   - [ ] DEMO_ENV_1 (기본 6개)
   - [ ] 추가 특징 테스트 (priority, steps_left 등)

3. **reward_type** (보상 함수)
   - [ ] Type 1: Tardiness 패널티
   - [ ] Type 2: On-time 보너스
   - [ ] Type 3: CR 기반
   - [ ] Type 7: Not-lateness 기반

4. **station_group** (제어할 머신 그룹)
   - [ ] `None`: 모든 머신 그룹
   - [ ] `"<Implant_128>"`: 특정 family
   - [ ] `"[STN001]"`: 특정 그룹

**실험 설계 템플릿:**
```bash
# 실험 1: num_actions 영향
python3 rl_train.py config_actions5.json
python3 rl_train.py config_actions9.json
python3 rl_train.py config_actions15.json

# 실험 2: reward_type 영향
python3 rl_train.py config_reward1.json
python3 rl_train.py config_reward2.json
python3 rl_train.py config_reward3.json
```

---

## 🔧 8단계: 커스터마이징 및 확장 (선택사항)

### 8.1 새로운 디스패칭 전략 구현

**목표:** EDD (Earliest Due Date) 전략 추가

**단계:**
1. [ ] `simulation/dispatching/dispatcher.py` 열기
2. [ ] 새 함수 추가:

```python
@staticmethod
def edd_ptuple_for_lot(lot, machine, time, r):
    """Earliest Due Date 전략"""
    return (
        0 if machine.min_runs_left is None or machine.min_runs_setup == lot.actual_step.setup_needed else 1,
        0 if lot.cqt_waiting is not None else 1,
        Dispatchers.get_setup(machine, lot, time),
        -lot.priority,
        lot.deadline_at,  # 마감일 빠른 순
    )
```

3. [ ] `dispatcher_map`에 등록:

```python
dispatcher_map = {
    'fifo': Dispatchers.fifo_ptuple_for_lot,
    'cr': Dispatchers.cr_ptuple_for_lot,
    'random': Dispatchers.random_ptuple_for_lot,
    'edd': Dispatchers.edd_ptuple_for_lot,  # 추가
}
```

4. [ ] 실험 실행:

```bash
pypy3 main.py --days 180 --dataset HVLM --dispatcher edd --seed 0 --alg l4m
```

5. [ ] 성능 비교

### 8.2 새로운 상태 특징 추가

**목표:** 로트의 남은 스텝 수를 상태에 포함

**단계:**
1. [ ] `simulation/gym/E.py` 열기
2. [ ] 새 컴포넌트 추가:

```python
class OPERATION_TYPE:
    # 기존 컴포넌트들...

    class STEPS_REMAINING:
        MEAN = 'steps_remaining_mean'
        MAX = 'steps_remaining_max'
        MIN = 'steps_remaining_min'
```

3. [ ] `simulation/gym/environment.py`의 `state` 속성 수정:

```python
action_type_state_lambdas = {
    # 기존 람다들...

    E.A.L4M.S.OPERATION_TYPE.STEPS_REMAINING.MEAN:
        lambda: mean([len(l.remaining_steps) for l in action]),
    E.A.L4M.S.OPERATION_TYPE.STEPS_REMAINING.MAX:
        lambda: max([len(l.remaining_steps) for l in action]),
}
```

4. [ ] 새 환경 설정 생성:

```python
# sample_envs.py에 추가
STATE_COMPONENTS_CUSTOM = (
    E.A.L4M.S.OPERATION_TYPE.NO_LOTS_PER_BATCH,
    E.A.L4M.S.OPERATION_TYPE.CR.MAX,
    E.A.L4M.S.OPERATION_TYPE.FREE_SINCE.MAX,
    E.A.L4M.S.OPERATION_TYPE.SETUP.MIN_RUNS_OK,
    E.A.L4M.S.OPERATION_TYPE.SETUP.NEEDED,
    E.A.L4M.S.OPERATION_TYPE.STEPS_REMAINING.MEAN,  # 추가
)

CUSTOM_ENV_1 = dict(
    action=E.A.CHOOSE_LOT_FOR_FREE_MACHINE,
    state_components=STATE_COMPONENTS_CUSTOM,
)
```

5. [ ] 새 환경으로 학습 실행

### 8.3 새로운 보상 함수 설계

**목표:** WIP (Work In Progress) 최소화 보상

**단계:**
1. [ ] `simulation/gym/environment.py`의 `step()` 메서드 수정
2. [ ] 새 reward_type 추가:

```python
def step(self, action):
    # ... (기존 코드)

    reward = 0
    if self.reward_type == 8:  # 새로운 타입
        # 완료된 로트당 +1000
        for i in range(self.lots_done, len(self.instance.done_lots)):
            reward += 1000

        # WIP 패널티 (active_lots가 많을수록 감소)
        reward -= len(self.instance.active_lots) * 0.1

        # On-time 보너스
        if lot.deadline_at >= lot.done_at:
            reward += 500

    # ... (나머지 코드)
```

3. [ ] Config에서 `"reward": 8` 설정
4. [ ] 학습 및 평가

### 8.4 플러그인 개발

**목표:** 실시간 차트 생성 플러그인

**단계:**
1. [ ] 새 파일 생성: `simulation/plugins/realtime_chart_plugin.py`

```python
from simulation.plugins.interface import IPlugin
import matplotlib.pyplot as plt
from collections import defaultdict

class RealtimeChartPlugin(IPlugin):
    def __init__(self):
        self.time_points = []
        self.wip_counts = []
        self.throughput_counts = []

    def on_sim_init(self, instance):
        self.start_time = instance.current_time

    def on_lot_done(self, instance, lot):
        # 데이터 수집
        current_day = (instance.current_time - self.start_time) / 3600 / 24
        self.time_points.append(current_day)
        self.wip_counts.append(len(instance.active_lots))
        self.throughput_counts.append(len(instance.done_lots))

    def on_sim_done(self, instance):
        # 차트 생성
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        ax1.plot(self.time_points, self.wip_counts)
        ax1.set_title('WIP over Time')
        ax1.set_xlabel('Days')
        ax1.set_ylabel('WIP Count')

        ax2.plot(self.time_points, self.throughput_counts)
        ax2.set_title('Throughput over Time')
        ax2.set_xlabel('Days')
        ax2.set_ylabel('Cumulative Throughput')

        plt.tight_layout()
        plt.savefig('simulation_chart.png')
        print("Chart saved to simulation_chart.png")

    def get_output_name(self):
        return None  # JSON 출력 없음
```

2. [ ] 플러그인 사용:

```python
# main.py 또는 rl_test.py에서
from simulation.plugins.realtime_chart_plugin import RealtimeChartPlugin

plugins = [RealtimeChartPlugin()]
instance = FileInstance(files, run_to, lot_for_machine, plugins)
```

---

## ⏱️ 예상 학습 기간

| 학습 수준 | 기간 | 포함 내용 |
|----------|------|----------|
| **최소 (핵심만)** | 2-3주 | 1-5단계, 실습 생략 가능 |
| **권장 (실습 포함)** | 4-6주 | 1-7단계, 모든 실습 포함 |
| **완전 숙달** | 2-3개월 | 1-8단계, 커스터마이징 포함 |

---

## 📝 학습 팁

### 효과적인 학습 방법

1. **단계별 진행**
   - 각 단계를 건너뛰지 말고 순서대로 진행
   - 이전 단계를 완전히 이해한 후 다음 단계로

2. **코드 읽기**
   - 직접 파일을 열어보고 주석 추가하며 이해
   - 중요한 함수는 디버거로 step-by-step 실행

3. **작은 실험**
   - 긴 시뮬레이션(365일)보다 짧은 실험(30-90일)으로 빠르게 반복
   - 변경 사항의 영향을 빠르게 확인

4. **결과 비교**
   - 변경 전후 결과를 항상 비교
   - 예상과 다른 결과는 원인 분석

5. **디버깅 도구**
   - `print()` 문: 간단한 값 확인
   - Python 디버거 (`pdb`): step-by-step 실행
   - Profiler (`pyinstrument`): 성능 병목 찾기

6. **문서화**
   - 배운 내용을 이 노트에 정리
   - 코드에 주석 추가
   - 실험 결과 기록

### 디버깅 팁

**Print 문 추가:**
```python
# instance.py의 dispatch() 메서드에
print(f"Dispatching {len(lots)} lots to machine {machine.idx}")
print(f"  Setup: {machine.current_setup} -> {lots[0].actual_step.setup_needed}")
print(f"  Processing time: {processing_time / 3600:.2f} hours")
```

**PDB 사용:**
```python
# 원하는 위치에 브레이크포인트 추가
import pdb; pdb.set_trace()

# 실행 후 명령어:
# n: 다음 줄
# s: 함수 내부로
# c: 계속 실행
# p variable_name: 변수 출력
# l: 현재 위치 코드 보기
```

---

## 🎓 학습 완료 후 할 수 있는 것

### 기술적 역량

- ✅ 반도체 제조 시뮬레이션 이해 및 분석
- ✅ 이벤트 기반 시뮬레이터 설계 및 구현
- ✅ 디스패칭 알고리즘 개발 및 평가
- ✅ 강화학습을 제조 스케줄링에 적용
- ✅ 복잡한 제약사항 모델링 (Setup, Batching, CQT 등)
- ✅ 실험 설계 및 통계 분석

### 프로젝트 확장 아이디어

1. **멀티 에이전트 RL**
   - 여러 머신 그룹을 독립적인 에이전트로
   - 협력적 디스패칭 전략

2. **딥러닝 아키텍처 개선**
   - Attention 메커니즘 추가
   - Graph Neural Network로 라우트 구조 모델링

3. **실시간 대시보드**
   - Web 기반 시뮬레이션 모니터링
   - 실시간 KPI 추적

4. **전이 학습**
   - HVLM에서 학습한 모델을 LVHM에 적용
   - Domain adaptation 기법

5. **다목적 최적화**
   - ACT, throughput, tardiness 동시 최적화
   - Pareto frontier 탐색

---

## 📚 참고 자료

### 논문
- Kopp et al. (2020), "SMT2020 Dataset", IEEE TSM
- [추가 관련 논문 링크]

### 문서
- OpenAI Gym: https://gym.openai.com/
- Stable-Baselines3: https://stable-baselines3.readthedocs.io/
- PyTorch: https://pytorch.org/docs/

### 코드 저장소
- 프로젝트: `/home/iamhjoo/project/PySCFabSim-release`
- GitHub: [프로젝트 URL]

---

## ✅ 학습 진행 체크리스트

### 1단계: 기초 개념
- [ ] 반도체 제조 용어 이해
- [ ] 시뮬레이션 개념 이해
- [ ] 데이터셋 구조 파악

### 2단계: 데이터 흐름
- [ ] 초기화 과정 추적
- [ ] 첫 실험 실행 성공
- [ ] 이벤트 흐름 이해

### 3단계: 디스패칭
- [ ] FIFO, CR 전략 이해
- [ ] L4M vs M4L 차이 파악
- [ ] 커스텀 dispatcher 작성

### 4단계: 제약사항
- [ ] Batching 로직 이해
- [ ] Setup 최적화 이해
- [ ] 제약 제거 실험 완료

### 5단계: RL 환경
- [ ] 환경 구조 이해
- [ ] 상태/액션 공간 파악
- [ ] 보상 함수 분석
- [ ] 환경 테스트 성공

### 6단계: RL 학습
- [ ] 실험 설정 생성
- [ ] 학습 실행 성공
- [ ] 체크포인트 평가 완료

### 7단계: 결과 분석
- [ ] 통계 분석 완료
- [ ] 성능 비교 매트릭스 작성
- [ ] 하이퍼파라미터 튜닝

### 8단계: 확장
- [ ] 새 dispatcher 추가
- [ ] 새 상태 특징 추가
- [ ] 새 보상 함수 추가
- [ ] 플러그인 개발

---

## 📊 학습 로그

### 날짜별 진행 상황

#### YYYY-MM-DD
- 학습 내용:
- 완료한 실습:
- 발견한 인사이트:
- 다음 할 일:

---

## 🔗 관련 노트

- [[PySCFabSim 아키텍처]]
- [[반도체 제조 공정]]
- [[강화학습 기초]]
- [[디스패칭 전략 비교]]

---

**마지막 업데이트:** 2025-11-18
**작성자:** Claude & User