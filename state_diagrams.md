# 🏭 PySCFabSim State Diagrams

## 1️⃣ Machine (장비) State Diagram

**설명:** 장비의 상태 전환을 보여줍니다. 장비는 Idle(유휴) → Processing(작업중) → Idle 또는 Breakdown/PM(고장/정비) 상태로 전환됩니다.

```mermaid
stateDiagram-v2
    [*] --> Idle: 시뮬레이션 시작

    Idle --> Processing: dispatch() 호출<br/>로트 배정됨
    Processing --> Idle: MachineDoneEvent<br/>작업 완료

    Processing --> Breakdown: BreakdownEvent<br/>고장 발생
    Processing --> PM: BreakdownEvent<br/>예방 정비

    Breakdown --> Idle: 수리 완료<br/>(length 시간 경과)
    PM --> Idle: 정비 완료<br/>(length 시간 경과)

    Idle --> Idle: waiting_lots에<br/>로트 추가됨

    note right of Idle
        상태: 사용 가능
        - waiting_lots 확인
        - 디스패칭 가능
    end note

    note right of Processing
        상태: 작업 중
        - 특정 로트 처리 중
        - events 리스트에
          MachineDoneEvent 존재
    end note

    note right of Breakdown
        상태: 고장
        - bred_time 증가
        - 모든 이벤트 지연
    end note

    note right of PM
        상태: 예방 정비
        - pmed_time 증가
        - 모든 이벤트 지연
    end note
```

> 💡 **핵심:** MachineDoneEvent가 Processing → Idle 전환을 트리거합니다.
> 장비가 Idle 상태가 되면 waiting_lots에 있는 다음 로트를 디스패칭할 수 있습니다.

---

## 2️⃣ Lot (로트) State Diagram

**설명:** 로트의 생명주기를 보여줍니다. 로트는 투입 대기 → 활성화 → 장비 대기 → 처리 → 다음 단계 또는 완료로 진행됩니다.

```mermaid
stateDiagram-v2
    [*] --> Dispatchable: 주문 생성

    Dispatchable --> Active: ReleaseEvent<br/>공장 투입 (release_at)
    Active --> WaitingForMachine: free_up_lots()<br/>현재 Step의 장비 찾기

    WaitingForMachine --> Processing: dispatch()<br/>장비에 배정됨
    Processing --> StepDone: LotDoneEvent<br/>현재 Step 완료

    StepDone --> WaitingForMachine: remaining_steps 존재<br/>(다음 Step으로)
    StepDone --> Done: remaining_steps 비어있음<br/>(모든 공정 완료)

    WaitingForMachine --> WaitingForMachine: 장비가 모두 사용 중

    Done --> [*]

    note right of Dispatchable
        상태: 투입 대기
        - dispatchable_lots 리스트
        - release_at < current_time
          되면 투입
    end note

    note right of Active
        상태: 활성화
        - active_lots 리스트
        - actual_step 설정됨
    end note

    note right of WaitingForMachine
        상태: 장비 대기
        - 특정 Machine의
          waiting_lots에 포함
        - free_since 시간 기록
    end note

    note right of Processing
        상태: 처리 중
        - 장비에서 작업 중
        - LotDoneEvent 예약됨
    end note

    note right of Done
        상태: 완료
        - done_lots 리스트
        - done_at 시간 기록
        - ACT, tardiness 계산
    end note
```

> 💡 **핵심:** LotDoneEvent가 현재 Step 완료를 트리거합니다.
> remaining_steps가 남아있으면 다음 Step으로, 없으면 완전히 완료됩니다.

---

## 3️⃣ 전체 이벤트 흐름 Diagram

**설명:** 시뮬레이션의 메인 루프입니다. ReleaseEvent → Dispatching → MachineDone/LotDone 이벤트가 순환하며 시뮬레이션이 진행됩니다.

```mermaid
stateDiagram-v2
    [*] --> Initialize: 시작

    Initialize --> EventLoop: 초기화 완료
    EventLoop --> CheckRelease: next_step()

    CheckRelease --> ProcessRelease: dispatchable_lots 존재
    CheckRelease --> ProcessEvent: 투입할 로트 없음

    ProcessRelease --> Dispatching: ReleaseEvent 처리

    ProcessEvent --> HandleMachineDone: MachineDoneEvent
    ProcessEvent --> HandleLotDone: LotDoneEvent
    ProcessEvent --> HandleBreakdown: BreakdownEvent

    HandleMachineDone --> Dispatching: free_up_machines()
    HandleLotDone --> Dispatching: free_up_lots()
    HandleBreakdown --> EventLoop: handle_breakdown()

    Dispatching --> MakeDecision: usable_machines &<br/>usable_lots 존재
    Dispatching --> EventLoop: 대기

    MakeDecision --> CreateEvents: dispatcher 전략<br/>로트 선택 & 배정
    CreateEvents --> EventLoop: Events 생성

    EventLoop --> SimDone: done_lots =<br/>전체 로트 수
    EventLoop --> CheckRelease: 계속

    SimDone --> [*]: 통계 출력

    note right of Initialize
        1. 데이터셋 로드
        2. Machine, Lot, Route 생성
        3. EventQueue 초기화
    end note

    note right of Dispatching
        핵심 의사결정 지점!
        - FIFO / CR / RL
        - priority tuple 계산
        - 최적 로트 선택
    end note

    note right of CreateEvents
        두 이벤트 생성:
        - MachineDoneEvent
        - LotDoneEvent
    end note
```

> 💡 **핵심:** next_step()이 다음 의사결정 지점까지 시뮬레이션을 진행시킵니다.
> usable_machines와 usable_lots가 모두 존재할 때 디스패칭이 발생합니다.

---

## 4️⃣ 디스패칭 의사결정 Diagram

**설명:** 디스패칭 과정에서 어떻게 로트를 선택하는지 보여줍니다. L4M(Lot-for-Machine)과 M4L(Machine-for-Lot) 두 가지 모드가 있습니다.

```mermaid
stateDiagram-v2
    [*] --> CheckUsable: 디스패칭 요청

    CheckUsable --> NoAction: usable_machines 또는<br/>usable_lots 없음
    CheckUsable --> GetCandidates: 둘 다 존재

    NoAction --> [*]: 대기

    GetCandidates --> L4M_Mode: lot_for_machine = True
    GetCandidates --> M4L_Mode: lot_for_machine = False

    L4M_Mode --> CalculatePriority: 각 Machine마다<br/>대기 로트 그룹화
    M4L_Mode --> CalculatePriority: 각 Lot마다<br/>가능한 Machine 확인

    CalculatePriority --> ApplyDispatcher: dispatcher 함수로<br/>priority tuple 계산

    ApplyDispatcher --> CheckConstraints: ptuple 기준 정렬

    CheckConstraints --> CheckMinRuns: min_runs 확인
    CheckMinRuns --> CheckSetup: setup 변경 확인
    CheckSetup --> CheckBatch: batching 확인

    CheckBatch --> ExecuteDispatch: 모든 제약 통과
    CheckMinRuns --> Penalty: min_runs 위반

    Penalty --> ExecuteDispatch: RL: -10 보상

    ExecuteDispatch --> ScheduleEvents: dispatch() 실행

    ScheduleEvents --> [*]: MachineDone &<br/>LotDone 예약

    note right of L4M_Mode
        Lot-for-Machine:
        - Machine 중심
        - "이 장비에 어떤 로트?"
        - RL 환경에서 사용
    end note

    note right of M4L_Mode
        Machine-for-Lot:
        - Lot 중심
        - "이 로트에 어떤 장비?"
        - Greedy 알고리즘
    end note

    note right of ApplyDispatcher
        Priority Tuple 예시:
        FIFO: (min_runs, cqt,
               setup_time, -priority,
               free_since)
        CR: (min_runs, cqt,
             setup_time, -priority,
             cr)
    end note
```

> 💡 **핵심:** dispatcher 전략(FIFO, CR, RL)이 priority tuple을 계산하고,
> 가장 우선순위가 높은 로트를 선택합니다. 제약사항 위반 시 패널티가 발생합니다.

---

## 5️⃣ Setup 상태 전환 Diagram

**설명:** 장비의 Setup 설정이 어떻게 변경되는지 보여줍니다. Setup 변경 시 setup_time이 소요되며, min_runs 제약이 있을 수 있습니다.

```mermaid
stateDiagram-v2
    [*] --> EmptySetup: 장비 초기화

    EmptySetup --> SetupA: Lot with Setup A 배정

    SetupA --> SetupA: 동일 Setup의 Lot 처리<br/>(setup_time = 0)
    SetupA --> SetupB: 다른 Setup의 Lot 배정<br/>(setup_time 소요)

    SetupB --> SetupA: Setup 변경<br/>(setup_time 소요)
    SetupB --> SetupB: 동일 Setup 계속

    SetupA --> MinRunsActive: min_runs 제약 활성화<br/>(min_runs_left = N)

    MinRunsActive --> MinRunsActive: 동일 Setup 처리<br/>(min_runs_left--)
    MinRunsActive --> SetupA: min_runs_left = 0<br/>제약 해제

    MinRunsActive --> Violation: 다른 Setup 시도
    Violation --> MinRunsActive: RL: -10 패널티

    note right of EmptySetup
        초기 상태
        - current_setup = ''
        - min_runs_left = None
    end note

    note right of SetupA
        Setup A 상태
        - current_setup = 'SU128_3'
        - setup 변경 없으면
          setup_time = 0
    end note

    note right of MinRunsActive
        Min Runs 제약 활성
        - min_runs_left = 5
        - 같은 Setup을 최소
          5번은 실행해야 함
        - 위반 시 패널티
    end note

    note right of Violation
        제약 위반!
        - RL: -10 reward
        - Greedy: 경고
        - 생산성 저하
    end note
```

> 💡 **핵심:** Setup 변경은 비용(setup_time)이 발생합니다.
> min_runs 제약이 있을 때 다른 Setup으로 변경하면 패널티가 발생하므로,
> 가능한 같은 Setup의 로트를 연속으로 처리하는 것이 유리합니다.

---

## 6️⃣ MachineDoneEvent vs LotDoneEvent 비교

**설명:** 두 이벤트의 차이를 시간 순서로 보여줍니다.

### 📊 일반 케이스 (Cascading 없음)

```mermaid
sequenceDiagram
    participant M as Machine #42
    participant L as Lot_3
    participant E as EventQueue

    Note over M,L: 시간 10:00 - 작업 시작
    M->>M: IDLE → PROCESSING
    L->>L: Step 17 (Implant)
    E->>E: MachineDoneEvent(10:30) 예약
    E->>E: LotDoneEvent(10:30) 예약

    Note over M,L: 시간 10:30 - 작업 완료 (동시 발생!)

    E->>M: MachineDoneEvent 처리
    M->>M: PROCESSING → IDLE
    M->>M: waiting_lots 확인
    M->>M: 다음 로트(Lot_15) 디스패칭

    E->>L: LotDoneEvent 처리
    L->>L: Step 17 완료
    L->>L: Step 18로 이동 (Dry_Etch)
    L->>L: Dry_Etch 장비의 waiting_lots에 추가
```

### 🔄 Cascading 케이스 (파이프라인)

```mermaid
sequenceDiagram
    participant M as Wet_Etch Machine
    participant L as Lot_3 (25 pieces)
    participant E as EventQueue

    Note over M,L: 시간 10:00 - 작업 시작
    M->>M: IDLE → PROCESSING
    L->>L: Step 2 (Wet_Etch) 시작
    E->>E: MachineDoneEvent(10:01) 예약
    E->>E: LotDoneEvent(10:25) 예약

    Note over M,L: 시간 10:01 - 첫 piece 완료
    E->>M: MachineDoneEvent 처리 ⭐
    M->>M: PROCESSING → IDLE
    M->>M: 다음 로트(Lot_15) 시작 가능!

    Note over L: Lot_3은 아직 처리 중 (나머지 24 pieces)

    Note over M,L: 시간 10:25 - 전체 완료
    E->>L: LotDoneEvent 처리 ⭐
    L->>L: Step 2 완전 완료
    L->>L: Step 3으로 이동
```

### 📦 Batching 케이스 (배치)

```mermaid
sequenceDiagram
    participant M as Diffusion Machine
    participant L1 as Lot_1
    participant L2 as Lot_2 ... Lot_100
    participant E as EventQueue

    Note over M,L2: 시간 10:00 - 배치 시작 (100개 로트)
    M->>M: IDLE → PROCESSING
    L1->>L1: Step 1 (Diffusion)
    L2->>L2: Step 1 (Diffusion)
    E->>E: MachineDoneEvent(18:00) 예약
    E->>E: LotDoneEvent(18:00) 예약

    Note over M,L2: 시간 18:00 - 배치 완료 (8시간 소요)

    E->>M: MachineDoneEvent 처리 ⭐
    M->>M: PROCESSING → IDLE (1대 장비)
    M->>M: 다음 배치 대기

    E->>L1: LotDoneEvent 처리 ⭐
    L1->>L1: Step 1 완료 → Step 2로
    E->>L2: LotDoneEvent 처리 (100개!)
    L2->>L2: Step 1 완료 → Step 2로
```

> 💡 **핵심 차이:**
> - **MachineDoneEvent**: 장비 관점 - "장비가 다시 사용 가능해요"
> - **LotDoneEvent**: 로트 관점 - "로트가 다음 단계로 가요"
> - **일반**: 두 이벤트가 동시 발생
> - **Cascading**: MachineDone이 먼저, LotDone이 나중
> - **Batching**: 1개 MachineDone, 여러 개 LotDone

---

## ✅ State Diagrams 요약

위 다이어그램들은 PySCFabSim의 핵심 동작 원리를 보여줍니다:

1. **Machine State**: 장비는 Idle/Processing/Breakdown/PM 상태를 순환
2. **Lot State**: 로트는 Dispatchable → Active → Waiting → Processing → Done 흐름
3. **Event Flow**: ReleaseEvent → Dispatching → MachineDone/LotDone 반복
4. **Dispatching**: L4M/M4L 모드에서 priority tuple로 최적 로트 선택
5. **Setup**: Setup 변경 비용과 min_runs 제약 관리
6. **Event 비교**: MachineDone(장비 중심) vs LotDone(로트 중심)

---

**마지막 업데이트:** 2025-11-18
