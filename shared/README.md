# 🌐 Shared (공유 - 시스템의 기반과 혈관)

## 📖 개요 (Overview)
`shared` 레이어는 MACH-VII 프로젝트의 가장 하부 계층으로, 시스템 전반에서 공통으로 사용되는 설정, 데이터 규격(DTO), 상태 중계 및 핵심 파이프라인 제어 로직을 포함합니다. 아키텍처 원칙인 **'단방향 데이터 흐름'**과 **'레이어 간 독립성'**을 유지하기 위한 핵심 인프라 역할을 수행합니다.

---

## 📂 주요 구성 요소 (Components)

### 1. ⚙️ [config.py](file:///d:/ARMY/MACH_VII_v2.0/shared/config.py) - 시스템 설정 및 경로 관리
시스템의 모든 '규칙'과 '지도'가 정의된 지점입니다.
- **`PathConfig`**: `pathlib`을 사용하여 프로젝트 전체의 7개 레이어 경로를 절대 경로로 관리합니다. 하드코딩을 방지하고 유연한 경로 참조를 제공합니다.
- **`GlobalConfig`**: `SIM_MODE`(시뮬레이션/실물 스위치), VLM 엔드포인트 및 모델명, 서버 포트, 로봇 IP 등 전역 설정을 중앙 집중 관리합니다.

### 2. 📝 [ui_dto.py](file:///d:/ARMY/MACH_VII_v2.0/shared/ui_dto.py) - 데이터 교환 규격
레이어 간, 특히 UI(React)와 백엔드(FastAPI) 간의 통신을 위한 표준 객체(DTO)를 정의합니다.
- **`UserRequestDTO`**: 모든 사용자 요청을 단일 규격으로 통일하여 레이어 진입 시 데이터의 정합성을 보장합니다.
- **`SystemConfigurationDTO`**: 로봇 대상(`RobotTarget`), 카메라 소스(`CameraSource`), 운영 모드(`OperationMode`) 등 인프라 설정을 묶어서 관리합니다.
- **Pydantic 활용**: 자동 데이터 검증 및 Enum-String 변환을 통해 명확한 인터페이스를 유지합니다.

### 3. 🧠 [pipeline.py](file:///d:/ARMY/MACH_VII_v2.0/shared/pipeline.py) - 7단계 파이프라인의 심장 (Refactored)
프로젝트의 핵심 철학인 **'Smart Brain, Dumb Body'**를 코드로 구현한 오케스트레이터입니다.
- **싱글톤 패턴**: 시스템 내 단 하나의 파이프라인 인스턴스만 존재하도록 보장합니다.
- **7-Layer Flow**: `Brain -> Strategy -> Expression -> Embodiment -> Memory` 순서로 데이터가 흐르도록 제어합니다.
- **최근 개선 사항**:
    - **컴포넌트 캐싱**: `emotion_controller`를 직접 변수로 관리하여 반복적인 검색 성능을 최적화했습니다.
    - **의도 확인 로직**: `intent` 변환 과정을 `if-elif-else` 구조로 리팩토링하여 가독성과 안전성을 높였습니다.

### 4. 🗣️ [intents.py](file:///d:/ARMY/MACH_VII_v2.0/shared/intents.py) - 시스템 표준 언어
로봇이 이해할 수 있는 행동의 최소 단위인 '의도(Intent)'를 정의합니다.
- **`ActionIntent` Enum**: `PICK_UP`, `MOVE`, `GREET` 등 시스템이 수행 가능한 표준 동작 목록입니다.
- **자연어 해석 (`from_str`)**: 사용자의 "가져와", "집어"와 같은 한국어 명령을 시스템 표준 의도로 매핑하는 휴리스틱 로직을 포함합니다.

### 5. 🎙️ [state_broadcaster.py](file:///d:/ARMY/MACH_VII_v2.0/shared/state_broadcaster.py) - 실시간 전광판
시스템 내부의 변화를 구독자(UI 등)에게 실시간으로 알리는 메시지 허브입니다.
- **Pub/Sub 패턴**: 하위 레이어나 브레인의 상태 변화를 `publish`하면, 등록된 `subscribers`에게 즉시 전파됩니다.
- **Chat/Thought Logging**: 사용자와의 대화 및 로봇의 내부 사고 과정(Thought)을 분리하여 기록함으로써 스마트한 UI 구현을 돕습니다. (최근 20개 로그 유지)

### 6. 🧹 [filters.py](file:///d:/ARMY/MACH_VII_v2.0/shared/filters.py) - 데이터 정제 유틸리티
센서 데이터의 물리적 노이즈를 제거하여 안정적인 제어를 가능하게 합니다.
- **`KalmanFilter`**: YOLO 등에서 들어오는 떨리는 좌표값(Flickering)을 수학적으로 예측/보정하여 로봇 팔이 부드럽게 움직이도록 필터링합니다.

---

## 🔗 상속 및 의존성 관계
- **의존성**: 이 패키지는 가급적 다른 레이어(Sensor, Brain 등)를 직접 참조하지 않고, 오직 설정과 전역 상태만을 공유하여 **순단(Strict Dependency)**을 유지합니다.
- **사용처**: 모든 상위 레이어에서 이 `shared` 패키지를 `import`하여 시스템의 규칙과 통신 수단을 상속받습니다.
