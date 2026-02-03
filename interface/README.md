# 🖥️ Interface (인터페이스 - 접점)

## ⚠️ 구현 상태 (Implementation Status)
- **현재 상태**: ✅ **구현 완료 (Implemented)**
    - 백엔드(`api_server`, `sim_client`)와 프론트엔드(`React App`)가 모두 정상 작동하며 연동되어 있습니다.

---

## 📖 개요 (Overview)
이 폴더는 **사용자**와 **로봇**을 연결하는 다리입니다.
웹 브라우저를 통해 로봇을 조종하고 상태를 볼 수 있게 해줍니다.

---

## 📂 파일 구조 및 상세 설명 (Structure & Files)

### 1. `backend/` (서버)
- **`api_server.py`**:
    - **역할**: 프론트엔드와 대화하는 **웹 서버(FastAPI)**입니다.
    - **통신 방식**: HTTP(명령 전송)와 WebSocket(실시간 상태 방송)을 모두 사용합니다.
    - **로직**: `/api/request` 로 들어온 JSON 명령을 `pipeline`이나 `robot_controller`로 전달합니다.
- **`sim_client.py`**:
    - **역할**: PyBullet 시뮬레이션 서버와 연결되는 **특수 클라이언트**입니다.
    - **필요성**: 로봇 로직은 파이썬인데, 시뮬레이터는 별도의 프로세스로 돌고 있어서 둘을 연결해줄 다리가 필요합니다.
    - **기능**: Socket.IO를 통해 시뮬레이터에서 로봇의 위치나 영상을 받아옵니다.

### 2. `frontend/` (웹 화면)
- **프로젝트 타입**: React 기반의 싱글 페이지 애플리케이션(SPA)입니다.
- **주요 폴더**:
    - **`components/`**: 화면을 구성하는 부품들.
        - `FaceControl.jsx`: 얼굴 렌더링 및 UI 통합 컨테이너.
        - `Face/`: 얼굴 그래픽 구성 요소 (Eye, Mouth, FaceRenderer).
        - `Controller/`: 파라미터 조절용 슬라이더 (FaceController) - *20종 표정 프리셋(10종 구현 완료 - 평온, 기쁨, 환희, 슬픔, 분노, 놀람, 의심, 고민, 공포, 지루함) 내장*.
    - **`constants/`**: 상수 정의 파일 모음.
        - `expressions.js`: 20가지 표정 프리셋의 Base(기본값) 및 Motion(진동) 파라미터 정의.

---

## ⚙️ 작동 원리 (Process Flow)

1. **사용자 입력**: 채팅창에 명령을 입력합니다.
2. **프론트엔드**: `UserRequestDTO`를 JSON으로 변환하여 `POST /api/request`로 보냅니다.
3. **백엔드(API Server)**: 요청을 받아 `RobotController`에게 전달합니다.
4. **실행 및 피드백**:
    - 로봇이 움직이는 동안 `sim_client.py`가 시뮬레이터에서 실시간 영상을 받아옵니다.
    - `api_server`가 이 영상을 웹소켓으로 프론트엔드에 다시 쏴줍니다.
5. **화면 갱신**: 사용자는 실시간으로 로봇이 움직이는 모습을 보게 됩니다.

### 시스템 아키텍처 (System Architecture)
```mermaid
graph TD
    User[사용자] -->|채팅/명령| UI[Frontend (React)]
    UI -->|REST API| Brain[Backend (Python)]
    Brain -->|상태 변화| EmotionController[Emotion Controller]
    
    subgraph "Phase 2: Emotion Bridge"
        EmotionController -->|1. 감정 벡터 분석| Mapper[Preset Mapper]
        Mapper -->|2. 프리셋 ID 결정 (e.g. Happy)| WS_Server[WebSocket Server]
        WS_Server -->|3. 실시간 전송 (JSON)| WS_Client[FaceContext (React)]
    end
    
    WS_Client -->|4. 표정 렌더링| FaceRenderer[Face Renderer (SVG)]
```

### 데이터 흐름 상세
1. **사용자 입력**: 채팅창에 명령을 입력합니다.
2. **프론트엔드**: `UserRequestDTO`를 JSON으로 변환하여 `POST /api/request`로 보냅니다.
3. **백엔드(API Server)**: 요청을 받아 `RobotController`에게 전달하고 로직을 수행합니다.
4. **감정 동기화 (Phase 2)**:
    - `EmotionController`가 로봇의 상태(성공, 실패, 대기 등)를 6차원 벡터로 변환합니다.
    - `get_closest_preset()` 함수가 벡터를 분석하여 가장 적절한 **표정 프리셋 ID**를 결정합니다.
    - `SystemSnapshot` 패킷에 이 ID를 담아 WebSocket으로 방송합니다.
5. **화면 갱신**: `FaceContext`가 패킷을 수신하면 즉시 해당 표정으로 전환합니다. (수동 제어 시에도 동기화 유지)

---

## 🔗 상속 및 관계 (Relationships)
- **상위**: 사용자(User)
- **연결**: `Shared` (UserRequestDTO 정의 사용), `Embodiment` (로봇 제어 요청)
- **특징**: 철저하게 **"UI is Dumb"** 원칙을 따릅니다. 화면은 예쁘게 보여주는 것(Rendering)과 사용자의 입력을 전달(Pass-through)하는 역할만 합니다. 모든 판단은 백엔드가 수행합니다.

---

## 🔮 향후 개선 과제 (Future Improvements)
감정 제어 시스템(Emotion Control System)은 현재 구현 완료되었으나, 지속적인 테스트와 디테일 수정이 필요합니다.

1.  **데이터베이스 스키마 확장 (DB Schema)**:
    - 감정 변화 이력(Emotion History)을 저장하기 위한 새로운 Node/Edge 설계가 필요할 수 있습니다.
    - 예: `(Agent)-[:FELT]->(EmotionEvent)`
2.  **보간 로직 튜닝 (Interpolation)**:
    - 현재의 선형/Deep Lerp 방식이 어색할 경우, Bezier Curve 기반의 더 정교한 보간으로 교체해야 합니다.
3.  **로깅 강화 (Logging)**:
    - 디버깅을 위해 프론트엔드/백엔드 인터랙션 로그를 더 세분화하여 기록해야 합니다.
