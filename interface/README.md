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
    - **`components/`**: 화면을 구성하는 부품들 (버튼, 슬라이더, 채팅창).
        - `ControlPanel`: 로봇 조작 버튼 모음.
        - `FaceController`: 얼굴 표정 디버깅용 슬라이더.
        - `ChatPanel`: AI와 대화하는 창.
    - **`Logic/`**: 백엔드와 통신하는 자바스크립트 코드.

---

## ⚙️ 작동 원리 (Process Flow)

1. **사용자 입력**: 웹에서 [잡기] 버튼을 클릭합니다.
2. **프론트엔드**: `UserRequestDTO` 형식의 JSON을 만들어 `POST /api/request`로 보냅니다.
3. **백엔드(API Server)**: 요청을 받아 `RobotController`에게 전달합니다.
4. **실행 및 피드백**:
    - 로봇이 움직이는 동안 `sim_client.py`가 시뮬레이터에서 실시간 영상을 받아옵니다.
    - `api_server`가 이 영상을 웹소켓으로 프론트엔드에 다시 쏴줍니다.
5. **화면 갱신**: 사용자는 실시간으로 로봇이 움직이는 모습을 보게 됩니다.

---

## 🔗 상속 및 관계 (Relationships)
- **상위**: 사용자(User)
- **연결**: `Shared` (UserRequestDTO 정의 사용), `Embodiment` (로봇 제어 요청)
- **특징**: 철저하게 **"UI is Dumb"** 원칙을 따릅니다. 화면은 예쁘게 보여주는 것(Rendering)과 사용자의 입력을 전달(Pass-through)하는 역할만 합니다.
