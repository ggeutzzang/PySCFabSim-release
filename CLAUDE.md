# CLAUDE.md

> Claude Code를 위한 PySCFabSim 프로젝트 가이드

## 📋 프로젝트 개요

PySCFabSim은 **반도체 제조(Semiconductor Fabrication) 시뮬레이터**로, 강화학습(RL)과 전통적인 디스패칭 전략을 사용하여 제조 공정을 최적화하는 연구 프로젝트입니다.

- **데이터셋**: SMT2020 (HVLM: High Volume Low Mix, LVHM: Low Volume High Mix)
- **목적**: FIFO, CR(Critical Ratio) 등 디스패칭 전략 비교 및 RL 기반 최적화
- **참고 논문**: Kopp et al. (2020), IEEE TSM

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

### 핵심 파일

```
simulation/
├── instance.py           # 시뮬레이션 중심 클래스 (이벤트 처리, 디스패칭)
├── file_instance.py      # SMT2020 데이터셋에서 Instance 생성
├── classes.py            # Machine, Lot, Step, Route 클래스
├── event_queue.py        # 이벤트 우선순위 큐
├── events.py             # MachineDone, LotDone, Breakdown, Release 이벤트
├── greedy.py             # Greedy 디스패칭 로직
├── stats.py              # 통계 계산 및 출력
│
├── dispatching/
│   ├── dispatcher.py         # FIFO, CR, Random 전략
│   ├── dm_lot_for_machine.py # Lot-for-Machine 매니저
│   └── dm_machine_for_lot.py # Machine-for-Lot 매니저
│
├── gym/
│   ├── environment.py    # OpenAI Gym RL 환경
│   ├── E.py              # 상태 컴포넌트 열거형
│   └── sample_envs.py    # 사전 정의 환경 (DEMO_ENV_1)
│
└── plugins/
    ├── interface.py      # IPlugin 인터페이스
    ├── cost_plugin.py    # 비용 계산
    └── wandb_plugin.py   # Weights & Biases 로깅

main.py                   # Greedy 실행 진입점
rl_train.py               # RL 학습
rl_test.py                # RL 평가
exp_set_gen.py            # 실험 설정 생성
eval_results.py           # 결과 집계
```

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
