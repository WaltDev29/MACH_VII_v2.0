# 🛠️ 아키텍쳐 준수 안정성 개선 계획 (Architecture-Compliant Stability Plan)

## 1. 아키텍쳐 위반 사항 분석 (Architecture Violation Analysis)
사용자의 지적이 정확합니다. 이전 계획에서 제안된 방식은 MACH-VII의 **7-Layer Pipeline** 및 **One-way Flow** 원칙을 일부 위배할 소지가 있었습니다. 이를 수정하여 아키텍쳐를 준수하면서도 문제를 해결하는 방안을 제시합니다.

### 1.1 Fast Track (위반 → 수정)
- **위반**: `Interface`(L7)나 `Pipeline`이 `Brain`(L3)을 우회하여 직접 하드웨어를 제어하려 함. 이는 "Brain이 의도를 결정한다"는 원칙 위배.
- **수정 (Reflex Brain)**: 
    - **Brain Layer 내부**에 **"반사 신경(Reflex Logic)"**을 구현합니다.
    - `LogicBrain.execute_task` 진입 시점(LLM 호출 전)에 키워드 기반의 빠른 판단 로직을 배치합니다.
    - Brain이 스스로 "생각보다 먼저" `STOP` 의도를 생성하여 파이프라인에 태우는 구조이므로 아키텍쳐를 준수합니다.

### 1.2 Event-Driven Memory (위반 → 수정)
- **위반**: `RobotController`(L6)가 `Brain`(L3)이나 `ChatHistory`에 직접 메시지를 주입(Reverse Flow). 하위 레이어가 상위 레이어를 호출하는 구조적 위반.
- **수정 (State-Based Proprioception)**: 
    - **State Layer(L2)**를 "공유 칠판"으로 활용합니다.
    - `RobotController`는 `SystemState.robot` (L2)의 상태값(`holding_object`, `last_action_result`)만 업데이트합니다.
    - `LogicBrain`은 다음 주기(Cycle)에 **SystemState를 관찰(Sense)**하여 상황을 인지합니다.
    - 이는 **[L6 → L2]** (상태 업데이트) 와 **[L2 ← L3]** (상태 관측)의 정방향 흐름들의 조합이므로 위배되지 않습니다.

---

## 2. 개선 로드맵 (Refined Roadmap)

### ✅ 2.1 Brain Reflex Logic (뇌내 반사 신경)
LLM의 추론 대기 시간을 제거하면서도 Brain의 제어권을 유지합니다.

- **위치**: `brain/logic_brain.py` -> `execute_task` 메서드 초입.
- **로직**:
    ```python
    # 0. Reflex Check (Thinking 이전에 즉각 반응)
    if any(k in task_command for k in ["멈춰", "정지", "stop"]):
        broadcaster.publish("agent_thought", "[Reflex] 위험 감지! 즉시 정합니다.")
        # 파이프라인을 통해 정식으로 STOP 의도 전달
        pipeline.process_brain_intent(ActionIntent.STOP)
        return
    ```

### ✅ 2.2 State-Based Feedback Loop (상태 기반 피드백)
로봇이 "잡았다"는 사실을 Brain이 알게 하려면, 로봇(몸)이 상태(State)를 바꾸고, Brain(뇌)이 그 상태를 읽어야 합니다.

1.  **`state/system_state.py` 확장**:
    - `RobotStatus` 클래스에 `holding_object: Optional[str]`, `last_action_status: str` 필드 추가.
2.  **`embodiment/robot_controller.py` 수정**:
    - 잡기 성공 시 -> `system_state.robot.holding_object = "duck"` 업데이트.
    - 동작 완료 시 -> `system_state.robot.last_action_status = "success"` 업데이트.
3.  **`brain/logic_brain.py` 컨텍스트 주입**:
    - LLM에게 제공되는 프롬프트(Context)에 시각 정보(`perception`) 뿐만 아니라, 고유수용감각(`proprioception`) 정보를 추가.
    - *"현재 상태: 오리를 잡고 있음. 마지막 행동: 성공함."*

### ✅ 2.3 Structured Tools & Prompt v2
이전 계획과 동일하게 유지하되, 구현 디테일을 보강합니다.

- **Pydantic 기반 도구 정의**: 문자열 파싱 실수 방지.
- **Few-Shot Prompting**: "박수" -> `clap` 루틴 매핑 예시 제공.

---

## 3. 실행 계획 (Execution Steps)

1.  **[1단계: Reflex]** `brain/logic_brain.py`에 키워드 기반 즉시 실행("Reflex") 로직 추가.
2.  **[2단계: State 확장]** `state/system_state.py`에 `holding_object`, `last_action_status` 필드 추가.
3.  **[3단계: 업데이트 연결]** `robot_controller.py`에서 동작 수행 후 해당 상태 필드를 업데이트하도록 로직 추가.
4.  **[4단계: 인지 연결]** `logic_brain.py`에서 `SystemState.robot` 정보를 프롬프트 컨텍스트에 포함.

이 계획은 **"Brain은 State를 보고 판단한다"**는 대원칙을 지키며 불안정성을 제거합니다.
