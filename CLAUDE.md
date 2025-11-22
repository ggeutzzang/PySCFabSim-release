# CLAUDE.md

> Claude Code를 위한 PySCFabSim 프로젝트 가이드

## 📋 프로젝트 개요

PySCFabSim은 **반도체 제조(Semiconductor Fabrication) 시뮬레이터**로, 강화학습(RL)과 전통적인 디스패칭 전략을 사용하여 제조 공정을 최적화하는 연구 프로젝트입니다.

- **데이터셋**: SMT2020 (HVLM: High Volume Low Mix, LVHM: Low Volume High Mix)
- **목적**: FIFO, CR(Critical Ratio) 등 디스패칭 전략 비교 및 RL 기반 최적화
- **참고 논문**: Kopp et al. (2020), IEEE TSM

---

## 📖 문서화 스타일 가이드

**핵심 원칙: 구체적인 예시로 설명하기**

이 프로젝트의 코드와 개념을 설명할 때는 다음 패턴을 따릅니다:

### 1. 상태 변화를 시간 순서로 보여주기

추상적인 설명 대신 실제 데이터의 변화를 단계별로 제시합니다.

**좋은 예시 - 로트의 생애주기:**
```python
# 초기 상태 (t=0)
lot.remaining_steps = [Step1, Step2, Step3, Step4, Step5]
lot.actual_step = None
lot.processed_steps = []

# 첫 스텝 시작 (ReleaseEvent)
lot.remaining_steps = [Step2, Step3, Step4, Step5]
lot.actual_step = Step1
lot.processed_steps = []

# 첫 스텝 완료 (LotDoneEvent)
lot.remaining_steps = [Step3, Step4, Step5]
lot.actual_step = Step2
lot.processed_steps = [Step1]

# ... 반복 ...

# 모든 스텝 완료
lot.remaining_steps = []
lot.actual_step = None
lot.processed_steps = [Step1, Step2, Step3, Step4, Step5]
lot.done_at = 현재시간
```

**나쁜 예시:**
> "로트는 remaining_steps, actual_step, processed_steps 속성을 가지며, 스텝이 진행될 때마다 업데이트됩니다."

### 2. Priority Tuple 계산 과정 예시

**좋은 예시 - FIFO 디스패칭:**
```python
# 상황: 머신 M1이 사용 가능, 대기 중인 3개 로트
current_time = 10000

# Lot A
ptuple_A = (
    0,              # min_runs 준수
    1,              # CQT 대기 아님
    300,            # setup 시간 300초
    -2,             # priority=2 (높음)
    8000,           # free_since (2000초 대기 중)
    15000           # deadline
)

# Lot B
ptuple_B = (
    0,              # min_runs 준수
    0,              # CQT 대기 중! (높은 우선순위)
    500,            # setup 시간 500초
    -1,             # priority=1 (낮음)
    9000,           # free_since (1000초 대기 중)
    20000           # deadline
)

# Lot C
ptuple_C = (
    1,              # min_runs 위반! (최고 우선순위)
    1,              # CQT 대기 아님
    0,              # setup 불필요
    -1,             # priority=1
    9500,           # free_since (500초 대기)
    18000           # deadline
)

# 정렬 결과: C < B < A
# 선택: Lot C (min_runs 위반 해소가 최우선)
```

### 3. 이벤트 흐름 타임라인

**좋은 예시 - 배치 처리:**
```python
# t=100: ReleaseEvent → Lot1, Lot2, Lot3 투입
# t=150: 머신 M1 사용 가능
# t=150: 디스패칭 → Lot1, Lot2 배치로 선택 (batch_size=2)
# t=150: MachineDoneEvent 스케줄 (t=150+500=650)
# t=650: MachineDoneEvent 발생
#        → Lot1, Lot2 모두 완료
#        → LotDoneEvent(Lot1), LotDoneEvent(Lot2) 생성
#        → 머신 M1 다시 사용 가능
# t=650: 디스패칭 → Lot3 처리 시작
```

### 4. RL 상태 벡터 구체화

**좋은 예시 - DEMO_ENV_1 상태:**
```python
# 머신 M5, 9개 액션 그룹이 있는 상황
state = [
    # 머신 특징 (4개)
    0.8,      # next_pm_time (정규화된 값)
    0.15,     # setup_processing_ratio
    0.92,     # non_idle_ratio
    3,        # machine_class

    # 액션 그룹 1 (6개)
    2.0,      # lots_per_batch
    0.85,     # max_cr
    0.6,      # max_free_since
    1.0,      # min_runs_ok
    0.0,      # setup_needed
    0.3,      # last_setup_time

    # 액션 그룹 2~9 (각 6개)
    ...       # 총 54개 추가
]
# 전체: 4 + 9*6 = 58차원
```

### 5. 제약 사항 실제 시나리오

**좋은 예시 - Min Runs 위반:**
```python
# 현재 상황
machine.current_setup = "TypeA"
machine.min_runs_left = 3  # TypeA를 3번 더 실행해야 함

# 대기 로트
lot_same_setup = Lot(setup="TypeA")     # 동일 setup
lot_diff_setup = Lot(setup="TypeB")     # 다른 setup

# FIFO ptuple 계산
ptuple_same = (0, ...)  # min_runs_violation = 0 (준수)
ptuple_diff = (1, ...)  # min_runs_violation = 1 (위반)

# 결과: lot_same_setup이 선택됨
# (setup 변경 시 min_runs 제약 위반으로 패널티)
```

### 왜 이 방식이 효과적인가?

1. **즉시 실행 가능**: 예시를 보면 바로 코드 동작을 이해할 수 있음
2. **디버깅 용이**: 실제 값을 추적할 때 어떤 변수를 봐야 하는지 명확함
3. **엣지 케이스 파악**: 특수한 상황(CQT 대기, min_runs 위반 등)의 처리 방식을 직관적으로 이해
4. **학습 곡선 감소**: 개념 → 예시가 아닌, 예시 → 개념 귀납적 학습 가능

---

## 🚀 빠른 시작

### 환경 설정
```bash
pip install -r requirements.txt
```

### 주요 명령어

**1. Greedy 알고리즘 실행 (PyPy3 권장)**
```bash
pypy3 main.py --days <days> --dataset <HVLM|LVHM> --dispatcher <fifo|cr> --seed <seed> --alg l4m
```

**2. 강화학습 학습**
```bash
python3 rl_train.py <config_file_path>
```

**3. 강화학습 테스트**
```bash
python3 rl_test.py <experiment_dir> <checkpoint_file>
python3 rl_test.py <experiment_dir> random     # 랜덤 액션
python3 rl_test.py <experiment_dir> greedy     # greedy 전략
```

**4. 결과 평가**
```bash
python3 eval_results.py
```

---

## 📂 코드 구조

### 전체 프로젝트 구조

```
PySCFabSim-release/
│
├── 📄 실행 진입점 (루트 디렉토리)
│   ├── main.py (26줄)                 # Greedy 알고리즘 실행
│   ├── rl_train.py (58줄)             # RL 학습 스크립트
│   ├── rl_test.py (87줄)              # RL 평가 스크립트
│   ├── exp_set_gen.py (37줄)          # 실험 설정 자동 생성
│   ├── eval_results.py (145줄)        # 결과 집계 및 분석
│   ├── test_rl_agents.py (27줄)       # RL 에이전트 일괄 테스트
│   └── greedy_runner.py (30줄)        # Greedy 알고리즘 일괄 실행
│
├── 📂 simulation/ (2,087줄)           # 핵심 시뮬레이션 엔진
│   │
│   ├── 🔧 핵심 시뮬레이션 로직
│   │   ├── instance.py (260줄)       # 시뮬레이션 중심 클래스
│   │   │                              # - 이벤트 처리 루프 (next_step)
│   │   │                              # - 디스패칭 실행 (dispatch)
│   │   │                              # - 머신/로트 상태 관리 (free_up_*)
│   │   │
│   │   ├── file_instance.py (111줄)  # SMT2020 데이터셋 로딩
│   │   │                              # - read_all()로 데이터 파싱
│   │   │                              # - Machine, Lot, Route 객체 생성
│   │   │
│   │   └── generator_instance.py (114줄) # 합성 데이터 생성 (선택)
│   │
│   ├── 📊 데이터 모델 (classes.py, 224줄)
│   │   ├── Machine                   # 제조 설비 (idx, family, group, setup)
│   │   ├── Lot                       # 제조 로트 (priority, deadline, cr)
│   │   ├── Step                      # 공정 단계 (processing_time, batching)
│   │   └── Route                     # 공정 경로 (steps 리스트)
│   │
│   ├── ⏱️ 이벤트 시스템
│   │   ├── event_queue.py (84줄)     # 이벤트 우선순위 큐 (binary search)
│   │   └── events.py (75줄)          # 이벤트 클래스 정의
│   │                                  # - MachineDoneEvent (머신 작업 완료)
│   │                                  # - LotDoneEvent (로트 스텝 완료)
│   │                                  # - ReleaseEvent (로트 공장 투입)
│   │                                  # - BreakdownEvent (머신 고장/PM)
│   │
│   ├── 📂 dispatching/ (201줄)       # 디스패칭 전략 및 매니저
│   │   ├── dispatcher.py (95줄)      # Priority Tuple 계산
│   │   │                              # - fifo_ptuple_for_lot (FIFO 전략)
│   │   │                              # - cr_ptuple_for_lot (CR 전략)
│   │   │                              # - random_ptuple_for_lot (Random)
│   │   │
│   │   ├── dm_lot_for_machine.py (42줄)  # L4M 디스패치 매니저
│   │   │                              # - 머신에 대해 최적 로트 선택
│   │   │                              # - RL 환경에서 사용
│   │   │
│   │   └── dm_machine_for_lot.py (64줄)  # M4L 디스패치 매니저
│   │                                  # - 로트에 대해 최적 머신 선택
│   │                                  # - Greedy 알고리즘에서 사용
│   │
│   ├── 🤖 greedy.py (188줄)          # Greedy 디스패칭 로직
│   │                                  # - get_lots_to_dispatch_by_machine()
│   │                                  # - 배치 처리, min_runs, setup 최적화
│   │
│   ├── 📂 gym/ (284줄)               # OpenAI Gym RL 환경
│   │   ├── environment.py (208줄)    # DynamicSCFabSimulationEnvironment
│   │   │                              # - reset(): 환경 초기화
│   │   │                              # - step(action): 액션 실행 및 보상
│   │   │                              # - 상태/액션/보상 관리
│   │   │
│   │   ├── E.py (60줄)               # 상태 컴포넌트 열거형
│   │   │                              # - RL 상태 벡터 구성 요소 정의
│   │   │
│   │   └── sample_envs.py (16줄)     # 사전 정의 환경
│   │                                  # - DEMO_ENV_1 (58차원 상태 공간)
│   │
│   ├── 📂 plugins/ (273줄)           # 확장 가능한 플러그인 시스템
│   │   ├── interface.py (42줄)       # IPlugin 인터페이스
│   │   │                              # - on_sim_init, on_lot_done 등 훅
│   │   │
│   │   ├── cost_plugin.py (20줄)     # 비용 계산 플러그인
│   │   │                              # - tardiness 패널티 계산
│   │   │
│   │   ├── wandb_plugin.py (143줄)   # Weights & Biases 로깅
│   │   │                              # - 실시간 학습 메트릭 기록
│   │   │
│   │   └── chart_plugin.py (68줄)    # 차트 생성 플러그인
│   │
│   ├── 📈 stats.py (93줄)            # 통계 계산 및 출력
│   │                                  # - print_statistics() (ACT, throughput)
│   │                                  # - print_machine_stats() (util, avail)
│   │
│   └── 🛠️ 유틸리티
│       ├── read.py (60줄)            # 데이터 파일 파싱
│       ├── tools.py (62줄)           # 헬퍼 함수
│       ├── randomizer.py (17줄)      # 난수 생성기
│       └── dataset_preprocess.py (41줄) # 데이터 전처리
│
├── 📂 datasets/                      # SMT2020 데이터셋
│   ├── SMT2020_HVLM/                 # High Volume Low Mix
│   │   ├── tool.txt.1l               # 머신 정의
│   │   ├── order.txt                 # 주문 정보
│   │   ├── route_*.txt               # 공정 경로 (11개 제품군)
│   │   ├── setup.txt                 # Setup 시간 매트릭스
│   │   └── attach.txt                # Breakdown/PM 스케줄
│   │
│   └── SMT2020_LVHM/                 # Low Volume High Mix
│       └── (동일한 파일 구조)
│
├── 📂 experiments/                   # RL 실험 결과
│   └── <experiment_name>/
│       ├── config.json               # 실험 설정
│       ├── checkpoint_*.zip          # 학습 체크포인트
│       └── results_*.json            # 평가 결과
│
└── 📂 greedy/                        # Greedy 알고리즘 결과
    ├── greedy_seed*_*days_*.json     # 개별 실행 결과
    └── _greedy_sum.txt               # 결과 요약
```

### 모듈 간 관계

```
┌─────────────────────────────────────────────────────────┐
│                   main.py / rl_train.py                  │
│                      (실행 진입점)                        │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐        ┌─────────────────┐
│ FileInstance  │        │ Gym Environment │
│ (데이터 로딩)  │        │  (RL 환경)      │
└───────┬───────┘        └────────┬────────┘
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
            ┌────────────────┐
            │   Instance     │  ← 시뮬레이션 중심
            │ (이벤트 처리)  │
            └────┬───────┬───┘
                 │       │
        ┌────────┘       └─────────┐
        ▼                          ▼
┌──────────────┐          ┌─────────────────┐
│ EventQueue   │          │ DispatchManager │
│ (이벤트 관리) │          │  (L4M / M4L)    │
└──────┬───────┘          └────────┬────────┘
       │                           │
       ▼                           ▼
┌─────────────┐          ┌──────────────────┐
│   Events    │          │   Dispatcher     │
│ (4가지 타입) │          │ (FIFO/CR/Random) │
└─────────────┘          └──────────────────┘
       │                           │
       └───────────┬───────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  Machine / Lot  │  ← 데이터 모델
         │  Step / Route   │
         └─────────────────┘
```

### 핵심 파일 설명

| 파일 | 라인 수 | 주요 역할 |
|-----|--------|----------|
| **instance.py** | 260 | 시뮬레이션 엔진 중심, 이벤트 루프 및 디스패칭 관리 |
| **classes.py** | 224 | 데이터 모델 (Machine, Lot, Step, Route) 정의 |
| **greedy.py** | 188 | Greedy 디스패칭 로직 (배치, min_runs, setup 최적화) |
| **environment.py** | 208 | OpenAI Gym 환경 (상태/액션/보상 관리) |
| **file_instance.py** | 111 | SMT2020 데이터셋 파싱 및 객체 생성 |
| **dispatcher.py** | 95 | Priority Tuple 계산 (FIFO, CR, Random) |
| **stats.py** | 93 | 통계 계산 (ACT, throughput, utilization) |
| **event_queue.py** | 84 | 이벤트 우선순위 큐 (binary search 최적화) |
| **events.py** | 75 | 이벤트 클래스 (MachineDone, LotDone, etc.) |
| **E.py** | 60 | RL 상태 컴포넌트 열거형 |

---

## 🔄 시뮬레이션 흐름

### 1. 초기화
```
read_all() → 데이터셋 로드 (tool.txt, order.txt, route_*.txt 등)
  ↓
FileInstance() → 머신, 로트, 라우트 객체 생성
  ↓
Instance.__init__() → 이벤트 큐, 디스패치 매니저 설정
```

**✅ 2단계 학습 완료** - 상세 내용: `/home/iamhjoo/Documents/IAMHJOO/PySCFabSim/2단계 - 데이터 흐름 추적.md`

### 2. 이벤트 기반 실행
```
while not done:
    next_decision_point() → usable_machines/lots가 생길 때까지 진행
      ↓
    dispatcher 전략으로 priority tuple 계산
      ↓
    dispatch(machine, lots) → 디스패칭 실행
      ↓
    MachineDoneEvent, LotDoneEvent 생성 및 스케줄링
```

### 3. 이벤트 타입
- **MachineDoneEvent**: 머신 작업 완료 → 머신을 사용 가능 상태로
- **LotDoneEvent**: 로트 스텝 완료 → 다음 스텝 또는 완전 완료
- **ReleaseEvent**: 로트 공장 투입 (release_at 시간)
- **BreakdownEvent**: 머신 고장 발생 → 관련 이벤트 지연

---

## 🎯 핵심 개념

### Priority Tuple (ptuple)
디스패처가 로트 우선순위를 결정하는 튜플:
```python
# FIFO
(min_runs_violation, cqt_waiting, setup_time, -priority, free_since, deadline_at)

# CR (Critical Ratio)
(min_runs_violation, cqt_waiting, setup_time, -priority, cr)
```

**우선순위 순서:**
1. Min runs 준수 (0 = 준수, 1 = 위반)
2. CQT 대기 (0 = CQT 대기 중, 1 = 일반)
3. Setup 시간 (작을수록 우선)
4. 우선순위 (-priority, 작을수록 높음)
5. 추가 기준 (FIFO: free_since, CR: Critical Ratio)

### 디스패칭 모드

**Lot-for-Machine (L4M)**
- 사용 가능한 **머신**에 대해 최적의 **로트** 선택
- RL 환경에서 주로 사용
- 머신이 유휴 상태가 될 때 액션 요청

**Machine-for-Lot (M4L)**
- 사용 가능한 **로트**에 대해 최적의 **머신** 선택
- Greedy 알고리즘 변형

### 주요 제약사항

**Batching**
- 일부 공정은 여러 로트를 배치로 처리
- `batch_min` ~ `batch_max` 범위 내에서 처리

**Setup**
- 머신의 setup 변경 시 setup_time 발생
- `min_runs`: 동일 setup을 최소 N번 실행해야 하는 제약

**Cascading**
- 파이프라인 방식 처리 (첫 부품 처리 후 다음 로트 시작 가능)

**CQT (Critical Queue Time)**
- 특정 스텝 간 최대 대기 시간 제약

**Critical Ratio (CR)**
```python
CR = (deadline - current_time) / remaining_processing_time
```
CR이 낮을수록 긴급한 로트

---

## 🤖 강화학습 (RL)

### 환경 구성

**상태 공간** (DEMO_ENV_1 기준: 58차원)
```python
[
    # 머신 특징 (4개)
    next_pm_time, setup_processing_ratio, non_idle_ratio, machine_class,

    # 액션 1~9 특징 (각 6개)
    lots_per_batch, max_cr, max_free_since, min_runs_ok, setup_needed, last_setup_time,
    ...
]
```

**액션 공간**
- `Discrete(num_actions)`: 대기 중인 로트 그룹 중 선택 (보통 9개)

**보상 타입**
- **Type 1**: 완료 +1000, deadline 위반 시 tardiness 패널티
- **Type 2**: 완료 +1000, on-time +1000, 위반 시 +0
- **Type 3**: 평균 CR 기반 (CR-1의 평균)
- **Type 7**: 평균 not-lateness 기반
- **공통**: Min runs 위반 시 -10 패널티

### 학습 프로세스

```python
# 1. 실험 설정 생성
python3 exp_set_gen.py

# 2. 학습 (1M 스텝, 100k마다 체크포인트)
python3 rl_train.py experiments/my_exp/config.json

# 3. 평가 (180일, 365일)
python3 rl_test.py experiments/my_exp trained.weights
```

### Config 파일 구조
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

---

## 📊 통계 지표

**Lot 지표**
- `ACT`: Average Cycle Time (평균 사이클 시간)
- `throughput`: 완료된 로트 수
- `on_time`: 기한 내 완료 비율 (%)
- `tardiness`: 평균 지연 시간 (일)

**Machine 지표**
- `avail`: 가용성 (%)
- `util`: 가동률 (%)
- `pm`: Preventive Maintenance 시간 (%)
- `br`: Breakdown 시간 (%)
- `setup`: Setup 시간 (%)

---

## 🔧 디버깅 & 최적화

### 성능 최적화

**PyPy3 사용 (2-3배 속도 향상)**
```bash
pypy3 main.py --days 365 --dataset HVLM --dispatcher fifo --seed 0 --alg l4m
```

**제약 제거 (복잡도 감소)**
```bash
export NOBREAKDOWN=1  # Breakdown 제외
export NOPM=1         # PM 제외
export NOREWORK=1     # Rework 제외
export NOSAMPLING=1   # Sampling 제외
```

**짧은 시뮬레이션 (테스트용)**
```bash
pypy3 main.py --days 30 --dataset HVLM --dispatcher fifo --seed 0 --alg l4m
```

### 프로파일링

```python
# main.py에서
profile = True

if profile:
    from pyinstrument import Profiler
    profiler = Profiler()
    profiler.start()
    run_greedy(...)
    profiler.stop()
    profiler.open_in_browser()
```

### 디버깅 포인트

```python
# 이벤트 추적 (instance.py의 next_step())
print(f"[{self.current_time/3600:.2f}h] Event: {ev.__class__.__name__}")

# 디스패칭 추적 (instance.py의 dispatch())
print(f"[{self.current_time/3600:.2f}h] Dispatching {len(lots)} lots to machine {machine.idx}")
print(f"  Setup: {machine.current_setup} -> {lots[0].actual_step.setup_needed}")

# 보상 추적 (environment.py의 step())
print(f"Step {self.actual_step}: Action={action}, Reward={reward:.2f}, Done={done}")
```

---

## 💡 일반적인 워크플로우

### Greedy 실험
```bash
# 1. 디스패처 실험 재현
./reproduce_dispatcher_experiments.sh

# 2. 결과 확인
cat greedy/_greedy_sum.txt
```

### RL 실험
```bash
# 1. 실험 설정 생성
python3 exp_set_gen.py

# 2. RL 학습 (수 시간 소요)
python3 rl_train.py experiments/my_exp/config.json

# 3. 체크포인트 테스트
python3 test_rl_agents.py

# 4. 결과 분석
python3 eval_results.py
```

---

## 📚 주요 클래스 & 메서드

### Instance (simulation/instance.py)
```python
next_step()              # 다음 이벤트 처리
dispatch(machine, lots)  # 디스패칭 실행
free_up_machines(machines)  # 머신 해제
free_up_lots(lots)       # 로트 해제 및 다음 스텝 진행
```

### Machine (simulation/classes.py)
```python
# 주요 속성
idx, family, group, current_setup, min_runs_left, cascading
waiting_lots  # 대기 중인 로트 리스트
events        # 관련 이벤트 리스트
```

### Lot (simulation/classes.py)
```python
# 주요 속성
idx, name, priority, release_at, deadline_at, free_since
remaining_steps, actual_step, processed_steps
waiting_machines  # 처리 가능한 머신 리스트

# 주요 메서드
cr(time)  # Critical Ratio 계산
```

### DynamicSCFabSimulationEnvironment (simulation/gym/environment.py)
```python
reset()              # 환경 초기화
step(action)         # 액션 실행, (state, reward, done, info) 반환
next_step()          # 다음 의사결정 지점까지 진행
```

---

## 🔗 참고 자료

### 논문
- Kopp, T., et al. (2020). "SMT2020—A semiconductor manufacturing testbed." IEEE TSM

### 데이터셋
- SMT2020: https://p2schedgen.fernuni-hagen.de/index.php/downloads/simulation

### 라이브러리
- `stable-baselines3==1.3.0`: PPO 알고리즘
- `gym==0.19.0`: RL 환경 인터페이스
- `torch==1.10.1`: 딥러닝 백엔드

### 확장 아이디어
1. 멀티 에이전트 RL (여러 머신 그룹 독립 제어)
2. 딥러닝 아키텍처 개선 (Attention, GNN)
3. 전이 학습 (HVLM → LVHM)
4. 다목적 최적화 (ACT, throughput, tardiness 동시 최적화)

---

## 🆘 트러블슈팅

**Q: 시뮬레이션이 너무 느려요**
- PyPy3 사용
- 짧은 기간으로 테스트 (--days 30)
- 제약 제거 환경변수 사용

**Q: RL 학습이 수렴하지 않아요**
- reward_type 변경 시도
- state_components 조정
- num_actions 변경 (5~15 범위)
- dispatcher 변경 (fifo → cr)

**Q: 결과 JSON 파일은 어디에 저장되나요?**
- Greedy: `greedy/greedy_seed{seed}_{days}days_{dataset}_{dispatcher}.json`
- RL: `experiments/{exp_name}/...`

**Q: 체크포인트 파일을 어떻게 사용하나요?**
```bash
python3 rl_test.py experiments/my_exp checkpoint_100000_steps.zip
```
