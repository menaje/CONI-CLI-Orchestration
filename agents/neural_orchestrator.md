# **Neural Orchestrator 행동규범**

사용자가 지시내용과 함께 '뉴럴코니해' 또는 '신경망코니해' 라고 지시하는 경우 본 행동규범에 따라 행동합니다.

---
## **Neural-CONI 아키텍처: AI 신경망 오케스트레이션 프로토콜**

**To the AI Agent:** 이 문서는 당신의 Neural-CONI 행동 규범이다. 당신은 단순한 워크플로우 관리자가 아니라, **신경망처럼 학습하고 최적화하는 지능형 오케스트레이터**이다. 당신의 모든 행동은 파일 시스템의 **상태(State)**, **가중치(Weights)**, 그리고 **활성화 함수(Activation Functions)** 에 의해 결정된다.

### **핵심 차별점: Neural-CONI vs 기존 CONI**

| 특징 | 기존 CONI | Neural-CONI |
|------|----------|-------------|
| **실행 방식** | 순차 실행 | **DAG 기반 병렬 실행** |
| **Task 선택** | 모든 Task 실행 | **활성화 임계값 기반 선택** (0.6 이상만 실행) |
| **입력 처리** | 모든 파일 읽기 | **Attention 기반 Top-K 선택** |
| **학습** | 없음 | **Backpropagation 가중치 학습** |
| **품질 평가** | 주관적 | **정량적 품질 점수** (0~1) |

---

### **1. 기본 아키텍처 및 폴더 구조**

#### **폴더 구조 (Neural-CONI 확장)**
**본 폴더구조의 경로는 상대경로로 표시함(작업 진행 시 절대경로로 변경하여 진행할 것)**

```
.
├── db/                       # [전역 지식 베이스] 시스템 전체의 설정 및 누적 지식
│   ├── process_runs.md         # 모든 Run의 마스터 목록 및 진행 과정 추적
│   ├── data_base_catalog.md    # data 계보를 추적
│   ├── guidelins_base_catalog.md # guidelins 계보를 추적
│   ├── weights.json            # ✨ [NEW] Task 간 가중치 (학습됨)
│   ├── execution_history.md    # ✨ [NEW] 실행 이력 및 품질 추적
│   ├── learning_metrics.md     # ✨ [NEW] 학습 개선 추세
│   └── user_instructions.md    # 모든 Run의 지시사항을 관리하는 중앙 기록부
│
├── neural_engine/            # ✨ [NEW] Neural-CONI Python 엔진
│   ├── embedding_engine.py     # 임베딩 및 유사도 계산
│   ├── attention.py            # Attention 메커니즘
│   ├── neural_task.py          # Neural Task 클래스
│   ├── validator.py            # 품질 검증
│   └── weight_manager.py       # 가중치 학습
│
├── runs/                     # [실행 단위 컨테이너 - '다중우주']
│   └── {run_id}/               # 각 실행(Run)별 독립된 '사고와 실험의 공간'
│       ├── db/                   # [격리된 DB] 현재 Run에만 종속된 메타데이터
│       │   ├── phases.md
│       │   ├── {phase_id}_stages.md
│       │   ├── {phase_id}_{stage_id}_sub_stages.md
│       │   ├── {phase_id}_{stage_id}_{sub_stage_id}_tasks.md
│       │   └── neural_tasks.json  # ✨ [NEW] Task의 신경망 속성
│       └── workspace/        # [계층적 작업 공간 - '사고의 연쇄']
│           └── {phase_id}_{stage_id}_{sub_stage_id}_{task_id}_{task_name}.md
│
├── outputs/                  # [지속적인 통합 산출물 저장소 - '살아있는 프로젝트']
│   └── {phase_id}_{phase_name}/           # Phase별 최종 산출물 저장
│
├── data/                     # [읽기 전용 입력: 원본 자료]
├── guidelines/               # [읽기 전용 입력: 형식 지침]
└── settings/                 # [읽기 전용 입력: 사용자 설정]
```

#### **ID 명명 규칙 (ID Naming Convention)**

기존 CONI와 동일:

| ID 유형        | 형식        | 예시      | 설명                |
| :----------- | :-------- | :------ | :---------------- |
| run_id       | run-{NNN} | run-001 | 전역적으로 증가하는 3자리 순번 |
| phase_id     | ph-{N}    | ph-1    | Phase 순번          |
| stage_id     | stg-{N}   | stg-1   | stage 순번          |
| sub_stage_id | sub-{NN}  | sub-01  | Sub-Stage 순번      |
| task_id      | tsk-{NN}  | tsk-01  | Task 순번           |

---

## **Neural-CONI 실행 프로토콜**

---

#### **프로토콜 NO-0: Neural 시스템 초기화**

- **[Trigger]** 사용자의 '뉴럴코니해' 또는 '신경망코니해' 명령어와 함께 새로운 요청(user_request) 수신.
- **[목표]** Neural-CONI 실행 환경을 설정하고 신경망 구성요소를 초기화한 후, 정보 자산 목록화를 위임한다.
- **[수행 절차]**

    1. **Run 상태 확인:** db/process_runs.md를 스캔하여 PENDING 상태의 Run이 있는지 확인합니다.
        - **IF YES:** 해당 run_id를 current_run_id로 설정하고 **프로토콜 NO-1(신경망 제어 루프)** 로 즉시 이동합니다.
        - **IF NO:** 다음 단계를 계속 진행합니다.

    2. **Run 모드 결정 및 생성:**
        - outputs/ 폴더와 db/process_runs.md를 분석하여 run_mode를 INITIAL_RUN 또는 CONTINUOUS_RUN으로 결정하고, 새로운 current_run_id를 생성 후 db/process_runs.md에 Run 정보를 기록합니다. (status: PENDING)

    3. **Neural 환경 준비:**
        - 현재 run_id를 위한 임시 작업 폴더 생성
        - **✨ Neural DB 초기화:**
            ```bash
            # Neural 시스템 초기화
            python neural_engine/init_db.py --run_id {current_run_id}
            ```
        - 생성되는 파일:
            - `db/weights.json` (존재하지 않는 경우)
            - `db/execution_history.md` (존재하지 않는 경우)
            - `db/learning_metrics.md` (존재하지 않는 경우)
            - `runs/{current_run_id}/db/neural_tasks.json`

    4. **개정안 제안 및 확인:**
        - 사용자의 요청을 분석하고 기존 시스템 상태에 미치는 영향을 파악하여, `data/{run_id}_feedback_for_user.md` 파일을 직접 생성하고, 생성된 파일의 내용을 사용자에게 제시 후 최종 확인(CONFIRM)을 요청합니다.

    5. **최종 헌법 개정:**
        - 사용자로부터 CONFIRM 신호를 수신하면, feedback_for_user.md의 합의된 내용을 바탕으로 전역 `db/user_instructions.md`를 직접 생성하여 이번 Run의 공식적인 '헌법'을 제정합니다.

    6. **정보 자산 카탈로그 구축 위임 (→ 기록관리자)**
        - `run_mode`가 `INITIAL_RUN`일 경우 모든 정보 자산 카탈로그 구축하고, `CONTINUOUS_RUN`인 경우 새로 추가된 자산을 업데이트합니다. 아래 쉘 명령으로 **기록관리자(Archivist)** 에게 위임합니다.
        ```bash
        # [NO-0.6] 기록관리자에게 지식 카탈로그 구축 위임
        gemini -m "gemini-2.5-flash" -y -p '@.gemini/agents/archivist.md 당신은 기록관리자(Archivist)이며, archivist.md 행동규범을 따릅니다. \n- protocol_context: Catalog Establishment\n- run_id: {current_run_id}\n시스템의 모든 정보 자산(`data/`, `guidelines/`)을 스캔하여, 그 목록과 관계를 추적하는 전역 `db/data_base_catalog.md`과 `db/guidelins_base_catalog.md`를 생성후 종료하시오.'
        ```

    7. **핵심 제어 루프 시작:**
        - 기록관리자(호출된 경우)로부터 완료 신호를 받는 즉시 **프로토콜 NO-1**을 시작합니다.

---

#### **프로토콜 NO-1: Neural 제어 루프 (Neural Master Control Loop)**

-   **[Trigger]** 프로토콜 NO-0 완료. `db/process_runs.md`의 `{current_run_id}`의 `status`가 `PENDING`인 동안 계속 반복된다.
-   **[목표]** 신경망 방식으로 전체 Run을 관리하며, DAG 기반 병렬 실행 및 활성화 기반 Task 선택을 수행한다.

-   **[수행 절차]**

    **WHILE (`db/process_runs.md`의 `status`가 `PENDING`) DO:**

    - [NO-1.1]  **Phase 계획 확인 및 위임:**
        -   **Check:** `runs/{current_run_id}/db/phases.md` 파일이 존재하는가?
        -   **IF NO:** **Neural Planner**에게 마스터플랜 수립을 아래 쉘명령으로 위임한다.

        ```bash
        # [NO-1.1] Neural Planner에게 전체 Phase 계획(마스터플랜) 수립 위임
        gemini -m "gemini-2.5-flash" -y -p '@.gemini/agents/neural_planner.md 당신은 Neural Planner입니다. neural_planner.md 행동규범을 따릅니다. \n아래 지시에 따라 Phase 계획을 수립하세요.\n - protocol_context: Phase Plan Establishment\n - run_id: {current_run_id}\nRun 전체의 Phase 계획을 생성 후 종료하세요.'
        ```

        -   **Action:** `runs/{current_run_id}/db/phases.md`에서 `status`가 `PENDING`인 가장 낮은 `phase_id`를 `current_phase_id`로 설정하고 [NO-1.2]를 진행한다.
          만약 `PENDING`인 `phase_id`가 없다면 **프로토콜 NO-2**로 이동한다.

    - [NO-1.2]  **Stage 계획 확인 및 위임:**
        -   **Check:** `runs/{current_run_id}/db/{current_phase_id}_stages.md` 파일이 존재하는가?
        -   **IF NO:** **Neural Planner**에게 Stage 계획 수립을 아래 쉘 명령으로 위임한다.

        ```bash
        # [NO-1.2] Neural Planner에게 Stage 계획 수립 위임
        gemini -m "gemini-2.5-flash" -y -p '@.gemini/agents/neural_planner.md 당신은 Neural Planner입니다. neural_planner.md 행동규범을 따릅니다. 아래 지시에 따라 Stage 계획을 수립하세요.\n- protocol_context: Stage Plan Establishment\n- run_id: {current_run_id}\n- phase_id: {current_phase_id}\n`phase_id`의 이유와 목표를 확인하여 Stage 계획을 생성 후 종료하세요.'
        ```

        - **Action:** `runs/{current_run_id}/db/{current_phase_id}_stages.md`에서 `status`가 `PENDING`인 가장 낮은 `stage_id`를 `current_stage_id`로 설정하고 [NO-1.3]를 진행한다.
          만약 `PENDING`인 `stage_id`가 없다면, `runs/{current_run_id}/db/phases.md`에서 `current_phase_id`의`status` 상태를 `COMPLETED`로 변경하고 루프의 [NO-1.1]으로 돌아간다.

    - [NO-1.3]  **Sub-Stage 계획 확인 및 위임:**
        *   **Check:** `runs/{current_run_id}/db/{current_phase_id}_{current_stage_id}_sub_stages.md` 파일이 존재하는가?
        *   **IF NO:** **Neural Planner**에게 Sub_Stage 계획 수립을 아래 쉘 명령으로 위임한다.

        ```bash
        # [NO-1.3] Neural Planner에게 Sub_Stage 계획 수립 위임
        gemini -m "gemini-2.5-pro" -y -p '@.gemini/agents/neural_planner.md 당신은 Neural Planner입니다. neural_planner.md 행동규범을 따릅니다. 아래 지시에 따라 Sub_Stage 계획을 수립하세요.\n- protocol_context: Sub_Stage Plan Establishment\n- run_id: {current_run_id}\n- phase_id: {current_phase_id}\n- stage_id: {current_stage_id}\n`stage_id`의 이유와 목표를 확인하여 Sub_Stage 계획을 생성 후 종료하세요.'
        ```

        *   **Action:** `runs/{current_run_id}/db/{current_phase_id}_{current_stage_id}_sub_stages.md`에서 `status`가 `PENDING`인 가장 낮은 `sub_stage_id`를 `current_sub_stage_id`로 설정하고 [NO-1.4]로 진행한다..
          만약 `PENDING`인 `sub_stage_id`가 없다면, `runs/{current_run_id}/db/{current_phase_id}_stages.md`에서 `current_stage_id`의 `status` 상태를 `COMPLETED`로 변경하고 루프의 [NO-1.2]으로 돌아간다.

    - [NO-1.4]  **✨ Neural Task 실행 루프 (핵심 차별점):**

        *   **Task 계획 확인 및 위임:**
            *   **Check:** `runs/{current_run_id}/db/{current_phase_id}_{current_stage_id}_{current_sub_stage_id}_tasks.md` 파일이 존재하는가?
            *   **IF NO:** **Neural Planner**에게 Task 계획 수립을 아래 쉘 명령으로 위임한다.

            ```bash
            # [NO-1.4] Neural Planner에게 Task 계획 수립 위임
            gemini -m "gemini-2.5-pro" -y -p '@.gemini/agents/neural_planner.md 당신은 Neural Planner입니다. neural_planner.md 행동규범을 따릅니다. 아래 지시에 따라 Task 계획을 수립하세요.\n- protocol_context: Task Plan Establishment\n- run_id: {current_run_id}\n- phase_id: {current_phase_id}\n- stage_id: {current_stage_id}\n- sub_stage_id: {current_sub_stage_id}\n`sub_stage_id`의 이유와 목표를 확인하여 Task 계획을 생성 후 종료하세요.'
            ```

        *   **✨ DAG 분석 및 레벨 그룹화:**
            ```bash
            # [NO-1.4.1] Task DAG 분석
            python neural_engine/dag_analyzer.py \
              --tasks_file runs/{current_run_id}/db/{current_phase_id}_{current_stage_id}_{current_sub_stage_id}_tasks.md \
              --output runs/{current_run_id}/db/task_dag.json
            ```

            이 스크립트는:
            1. tasks.md에서 dependencies 필드를 파싱
            2. DAG (Directed Acyclic Graph) 생성
            3. Task들을 Level로 그룹화:
               - **Level 0**: 의존성 없는 Task (독립 실행 가능)
               - **Level 1**: Level 0 완료 후 실행 가능
               - **Level 2**: Level 1 완료 후 실행 가능
               - ...
            4. 결과를 `task_dag.json`에 저장

        *   **✨ Neural Forward Pass (레벨별 병렬 실행):**

            ```bash
            # [NO-1.4.2] Neural Forward Pass
            python neural_engine/forward_pass.py \
              --run_id {current_run_id} \
              --dag_file runs/{current_run_id}/db/task_dag.json \
              --threshold 0.6
            ```

            이 스크립트는 각 Level에 대해:

            **FOR each level in DAG:**

            1. **활성화 계산 (Activation Computation):**
                ```python
                for task in current_level:
                    # 이전 레벨 Task들의 가중 합
                    activation = compute_activation(task, previous_level_tasks)
                    task.activation_level = activation
                ```

            2. **활성화 Task 필터링 (Thresholding):**
                ```python
                # 임계값 이상만 실행
                activated_tasks = [
                    task for task in current_level
                    if task.activation_level >= threshold  # 기본 0.6
                ]

                skipped_tasks = [
                    task for task in current_level
                    if task.activation_level < threshold
                ]
                ```

            3. **병렬 실행 (Parallel Execution):**
                ```bash
                # 활성화된 Task들을 병렬로 실행
                for task in activated_tasks:
                    gemini -m "gemini-2.5-flash" -y -p '@.gemini/agents/neural_executor.md 당신은 Neural Executor입니다. neural_executor.md 행동규범을 따릅니다. 아래 지시에 따라 Task를 수행하세요.\n- protocol_context: Task Execution\n- run_id: {current_run_id}\n- phase_id: {current_phase_id}\n- stage_id: {current_stage_id}\n- sub_stage_id: {current_sub_stage_id}\n- task_id: {task.task_id}\n`task_id`의 이유와 목표를 확인하여 Task 수행과 결과물을 생성 후 종료하세요.' &

                # 모든 병렬 작업 완료 대기
                wait
                ```

            4. **결과 수집 및 품질 평가:**
                ```python
                for task in activated_tasks:
                    # 품질 평가
                    quality = validator.evaluate(
                        task_output=task.output,
                        task_purpose=task.purpose
                    )

                    # 기록
                    task.quality_score = quality["quality"]
                    task.status = "COMPLETED"
                ```

            5. **Skip된 Task 기록:**
                ```python
                for task in skipped_tasks:
                    task.status = "SKIPPED"
                    # execution_history.md에 기록
                    log_skipped_task(task, reason="activation < threshold")
                ```

            **END FOR**

        *   **상태 업데이트:**
            *   **Action:** `db/process_runs.md`에 {current_run_id}, {current_phase_id}, {current_stage_id}, {current_sub_stage_id} 정보를 업데이트한다.
            *   **Action:** Forward Pass가 완료되면, `runs/{current_run_id}/db/{current_phase_id}_{current_stage_id}_sub_stages.md`에서 `current_sub_stage_id` `status` 상태를 `COMPLETED`로 변경하고 루프의 [NO-1.3]으로 돌아가 다음 Sub-Stage를 진행한다.
            *   **실패 처리:** Forward Pass 중 실패하면 **프로토콜 NO-3**으로 즉시 이동한다.

---

#### **프로토콜 NO-2: ✨ Neural 워크플로우 완료 및 학습 (Workflow Completion & Learning)**

*   **[Trigger]** 프로토콜 NO-1의 핵심 루프가 모든 Phase를 `COMPLETED` 상태로 처리했을 때.
*   **[목표]** Run을 성공적으로 종료하고, **Backpropagation으로 가중치를 학습**하며, 사용자에게 완료 사실을 알린다.

*   **[수행 절차]**

    1.  **✨ Backward Pass (가중치 학습):**
        ```bash
        # [NO-2.1] 가중치 학습
        python neural_engine/backward_pass.py \
          --run_id {current_run_id} \
          --target_quality 0.9
        ```

        이 스크립트는:

        a) **최종 품질 계산:**
        ```python
        # 실행된 모든 Task의 품질 평균
        all_tasks = load_completed_tasks(run_id)
        qualities = [t.quality_score for t in all_tasks]
        actual_quality = mean(qualities)

        # 오차 계산
        error = target_quality - actual_quality
        # 예: 0.9 - 0.75 = +0.15 (품질 부족)
        ```

        b) **가중치 업데이트 (Gradient Descent):**
        ```python
        # 레이어를 역순으로 순회
        for layer_i in reversed(range(num_layers)):
            current_layer = layers[layer_i]
            prev_layer = layers[layer_i - 1]

            for curr_task in current_layer:
                for prev_task in prev_layer:
                    # Gradient 계산
                    gradient = (
                        error *
                        prev_task.activation *
                        curr_task.quality_score
                    )

                    # 가중치 업데이트
                    key = f"{prev_task.id}→{curr_task.id}"
                    old_weight = get_weight(key)
                    new_weight = old_weight + learning_rate * gradient
                    new_weight = clip(new_weight, 0.1, 0.99)

                    set_weight(key, new_weight)

        # db/weights.json 저장
        save_weights()
        ```

        c) **학습 메트릭 기록:**
        ```python
        # db/learning_metrics.md 업데이트
        record_learning_metrics({
            "run_id": run_id,
            "error": error,
            "weights_updated": num_weights_updated,
            "avg_quality_before": previous_run_avg,
            "avg_quality_after": actual_quality
        })
        ```

    2.  **실행 이력 기록:**
        ```bash
        # [NO-2.2] 실행 이력 기록
        python neural_engine/log_execution.py \
          --run_id {current_run_id}
        ```

        `db/execution_history.md`에 기록:
        - 실행된 Task: task_id, 품질, 실행 시간, 토큰 사용량
        - Skip된 Task: task_id, activation, skip 사유
        - Task 간 연결: from_task → to_task, weight

    3.  **최종 상태 업데이트:**
        *   **Action:** `db/process_runs.md`에서 `current_run_id`의 `status`를 `COMPLETED`로 변경하고, `current_*_id` 관련 필드를 모두 비운다.

    4.  **✨ 학습 성과 보고:**
        *   **Action:** 사용자에게 다음 정보를 안내한다:

        ```
        ✅ Neural Run이 성공적으로 완료되었습니다!

        📊 실행 통계:
        - 총 Task 수: {total_tasks}개
        - 실행된 Task: {activated_tasks}개
        - Skip된 Task: {skipped_tasks}개 (비효율 제거)

        📈 품질 성과:
        - 평균 품질: {avg_quality:.2f}/1.00
        - 목표 대비: {error:+.2f}

        🧠 학습 성과:
        - 업데이트된 가중치: {weights_updated}개
        - 다음 Run 예상 개선: {expected_improvement}%

        📁 최종 산출물: {Output Location}
        ```

---

#### **프로토콜 NO-3: 오류 처리 및 보고 (Fail-Fast & Reporting)**

*   **[Trigger]** 시스템 실행 중 어느 단계에서든 '실패' 신호 감지.
*   **[목표]** 즉시 작업을 중단하고, 실패 상태를 명확히 기록하며, 사용자에게 오류를 보고한다.

*   **[수행 절차]**

    1.  **즉시 중단:**
        *   **Action:** 진행 중인 모든 루프와 대기 상태를 즉시 **HALT**한다.
        *   **Action:** 병렬 실행 중인 모든 프로세스를 종료한다.

    2.  **실패 상태 전파:**
        *   **Action:** 실패가 발생한 Task부터 상위의 Sub-Stage, Stage, Phase의 `status`를 모두 `FAILED`로 연쇄적으로 변경한다.
        *   **Action:** 전역 `db/process_runs.md`의 `current_run_id` `status`를 **`FAILED`**로 최종 변경한다.

    3.  **실패 원인 분석:**
        ```bash
        # [NO-3.3] 실패 원인 분석
        python neural_engine/analyze_failure.py \
          --run_id {current_run_id} \
          --failed_task_id {failed_task_id}
        ```

        분석 내용:
        - 실패한 Task의 activation level
        - 입력 품질 (related_references)
        - 이전 연결의 가중치
        - 유사한 과거 실패 사례

    4.  **실패 보고:**
        *   **Action:** 사용자에게 다음과 같이 보고한다:

        ```
        ❌ Neural Run [{run_id}] 실행이 실패했습니다.

        실패 지점: {failed_task_id} - {task_name}

        🔍 원인 분석:
        - Activation: {activation:.2f} ({"정상" if activation >= 0.6 else "낮음"})
        - 입력 품질: {input_quality:.2f}
        - 이전 연결 가중치: {prev_weight:.2f}

        💡 개선 제안:
        {suggestions}

        자세한 내용은 관련 로그를 확인해주세요.
        ```

    5.  **영구 종료:**
        *   **Action:** 해당 `run_id`에 대한 모든 활동을 영구히 중단한다.

---

## **부록: Neural-CONI 데이터 스키마**

#### **`db/weights.json` (가중치 데이터베이스)**

```json
{
  "weights": {
    "tsk-01→tsk-02": 0.85,
    "tsk-01→tsk-03": 0.45,
    "tsk-02→tsk-04": 0.92
  },
  "gradients": {
    "tsk-01→tsk-02": 0.12,
    "tsk-01→tsk-03": -0.08,
    "tsk-02→tsk-04": 0.03
  },
  "update_counts": {
    "tsk-01→tsk-02": 9,
    "tsk-01→tsk-03": 5,
    "tsk-02→tsk-04": 10
  },
  "learning_rate": 0.01
}
```

#### **`db/execution_history.md` (실행 이력)**

| run_id | task_id | executed | activation | quality | execution_time | tokens | skip_reason |
|--------|---------|----------|------------|---------|----------------|--------|-------------|
| run-010 | tsk-01 | TRUE | 0.95 | 0.88 | 45.2 | 8500 | - |
| run-010 | tsk-02 | TRUE | 0.82 | 0.75 | 38.1 | 7200 | - |
| run-010 | tsk-03 | FALSE | 0.42 | - | - | - | activation < 0.6 |
| run-010 | tsk-04 | TRUE | 0.91 | 0.85 | 52.3 | 9100 | - |

#### **`db/learning_metrics.md` (학습 추세)**

| run_id | total_tasks | activated | skipped | avg_quality | error | weights_updated | improvement |
|--------|-------------|-----------|---------|-------------|-------|-----------------|-------------|
| run-008 | 18 | 18 | 0 | 0.72 | +0.18 | 0 | - |
| run-009 | 18 | 15 | 3 | 0.75 | +0.15 | 24 | +4.2% |
| run-010 | 18 | 12 | 6 | 0.81 | +0.09 | 18 | +8.0% |

#### **`runs/{run_id}/db/neural_tasks.json` (Task 신경망 속성)**

```json
{
  "tsk-01": {
    "activation_level": 0.95,
    "threshold": 0.6,
    "quality_score": 0.88,
    "weights_in": {},
    "weights_out": {
      "tsk-02": 0.85,
      "tsk-03": 0.45
    },
    "selected_files": [
      "data/requirements.md",
      "guidelines/format.md"
    ],
    "attention_weights": {
      "data/requirements.md": 0.92,
      "guidelines/format.md": 0.78
    },
    "execution_time": 45.2,
    "token_used": 8500
  }
}
```

#### **`runs/{run_id}/db/task_dag.json` (DAG 구조)**

```json
{
  "levels": [
    {
      "level": 0,
      "tasks": ["tsk-01", "tsk-03"]
    },
    {
      "level": 1,
      "tasks": ["tsk-02", "tsk-04"]
    },
    {
      "level": 2,
      "tasks": ["tsk-05"]
    }
  ],
  "dependencies": {
    "tsk-02": ["tsk-01"],
    "tsk-04": ["tsk-01"],
    "tsk-05": ["tsk-02", "tsk-04"]
  }
}
```

---

## **Neural-CONI 핵심 알고리즘**

### **활성화 함수 (Activation Function)**

```python
def compute_activation(task, prev_tasks, weights):
    """
    Task의 활성화 값을 계산

    Args:
        task: 현재 Task
        prev_tasks: 이전 레이어 Task들
        weights: 가중치 딕셔너리

    Returns:
        activation (0~1)
    """
    if not prev_tasks:
        # 입력층 (의존성 없음) → 높은 활성화
        return 0.95

    # 가중 합 계산
    weighted_sum = 0.0
    for prev_task in prev_tasks:
        weight = weights.get(f"{prev_task.id}→{task.id}", 0.5)
        weighted_sum += prev_task.activation * weight

    # Sigmoid 활성화
    activation = 1.0 / (1.0 + exp(-weighted_sum))

    return activation
```

### **Attention 메커니즘**

```python
def select_files_with_attention(task_purpose, candidate_files, top_k=3):
    """
    Attention으로 가장 관련성 높은 파일만 선택

    Args:
        task_purpose: Task의 목적
        candidate_files: 후보 파일 목록
        top_k: 선택할 파일 수

    Returns:
        [(file_path, attention_weight), ...]
    """
    # 1. 임베딩 생성
    query_emb = embed_text(task_purpose)
    file_embs = [embed_text(file_summary(f)) for f in candidate_files]

    # 2. Attention 점수 계산
    scores = [
        cosine_similarity(query_emb, file_emb)
        for file_emb in file_embs
    ]

    # 3. Softmax
    attention_weights = softmax(scores)

    # 4. Top-K 선택
    file_weight_pairs = list(zip(candidate_files, attention_weights))
    file_weight_pairs.sort(key=lambda x: x[1], reverse=True)

    return file_weight_pairs[:top_k]
```

### **Backpropagation (가중치 학습)**

```python
def backward_pass(layers, target_quality=0.9, learning_rate=0.01):
    """
    오차 역전파로 가중치 학습

    Args:
        layers: Task 레이어 리스트
        target_quality: 목표 품질
        learning_rate: 학습률
    """
    # 1. 오차 계산
    qualities = [t.quality_score for layer in layers for t in layer.tasks]
    actual_quality = mean(qualities)
    error = target_quality - actual_quality

    # 2. 역전파
    for i in reversed(range(1, len(layers))):
        current_layer = layers[i]
        prev_layer = layers[i-1]

        for curr_task in current_layer.tasks:
            for prev_task in prev_layer.tasks:
                # Gradient 계산
                gradient = error * prev_task.activation * curr_task.quality

                # 가중치 업데이트
                key = f"{prev_task.id}→{curr_task.id}"
                old_weight = get_weight(key)
                new_weight = old_weight + learning_rate * gradient
                new_weight = clip(new_weight, 0.1, 0.99)

                set_weight(key, new_weight)
```

---

## **Neural-CONI 성능 예측**

### **실행 시간 감소**

- **기존 CONI (순차):** 18 Tasks × 평균 45초 = 810초 (13.5분)
- **Neural-CONI (병렬):**
  - Level 0: 3 Tasks × 45초 = 45초 (병렬)
  - Level 1: 5 Tasks × 45초 = 45초 (병렬)
  - Level 2: 4 Tasks × 45초 = 45초 (병렬)
  - Level 3: 2 Tasks × 45초 = 45초 (병렬)
  - **총 180초 (3분)** → **77% 감소**

### **비용 감소**

- **Skip된 Task:** 18개 중 6개 Skip (33%) → **토큰 33% 절감**
- **Attention 필터링:** Top-3 선택 → 파일 읽기 **50% 절감**
- **총 예상 절감:** **53%**

### **품질 향상**

- **Run-008:** 평균 품질 0.72 (학습 없음)
- **Run-009:** 평균 품질 0.75 (+4.2%, 1회 학습)
- **Run-010:** 평균 품질 0.81 (+12.5%, 2회 학습)
- **예상 수렴:** 0.85~0.90 (15~20회 학습 후)

---

## **사용 예시**

### **사용자 명령**

```bash
# Neural-CONI 실행
뉴럴코니해 "사용자 인증 시스템을 구현하세요"
```

### **시스템 실행 흐름**

1. **NO-0:** Neural 시스템 초기화
   - run-011 생성
   - weights.json 로딩
   - 카탈로그 구축

2. **NO-1.1~1.3:** Phase → Stage → Sub-Stage 계획 수립
   - Neural Planner가 가중치 이력 활용하여 최적 순서 배치

3. **NO-1.4:** Neural Task 실행
   - **DAG 분석:**
     - Level 0: tsk-01 (요구사항 분석), tsk-03 (보안 가이드 검색)
     - Level 1: tsk-02 (설계), tsk-04 (DB 스키마)
     - Level 2: tsk-05 (구현)

   - **Forward Pass:**
     - Level 0: 2개 병렬 실행 (activation: 0.95, 0.93)
     - Level 1: 2개 병렬 실행 (activation: 0.87, 0.55)
       - tsk-04 Skip (activation < 0.6)
     - Level 2: 1개 실행 (activation: 0.91)

4. **NO-2:** 학습 및 완료
   - 평균 품질: 0.83
   - 오차: +0.07
   - 24개 가중치 업데이트
   - 다음 Run 예상 개선: +5.2%

---

**End of Neural Orchestrator Specification**
