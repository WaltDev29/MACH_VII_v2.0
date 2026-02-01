# 🚀 MACH-VII v2.0 실행 가이드 (Run Guide)

이 문서는 새로운 담당자가 개발 환경을 구축하고 프로젝트를 실행하는 구체적인 절차를 설명합니다.

## ✅ 정상 실행 상태 체크

아래 3가지를 모두 만족하면 정상 실행입니다.

1. Backend 터미널에 `[Main] System Started` 로그 출력
2. Frontend 콘솔에 `WebSocket Connected` 로그 출력
3. UI에서 얼굴 표정이 60fps로 부드럽게 갱신됨


## 1. 필수 환경 준비 (Prerequisites)

이 프로젝트는 다음 환경에서 구동되도록 설계되었습니다.

1.  **OS**: Windows 10/11 (권장) 또는 Linux/macOS
2.  **Package Manager**: Anaconda (또는 Miniconda)
3.  **Runtime**: Node.js v18 이상 (프론트엔드용)
4.  **Database**: Docker Desktop (FalkorDB 실행용)

---

## 2. 백엔드(Backend) 환경 설정 및 실행

### 2.1 데이터베이스 실행 (필수)
프로젝트 루트에서 Docker Compose를 사용하여 DB를 실행합니다.

```bash
docker-compose up -d
```
> **참고**: `docker-compose.yml` 설정을 통해 데이터베이스의 데이터는 로컬 `memory/data` 폴더에 영구적으로 보존됩니다. 컨테이너를 삭제해도 로컬 폴더를 지우지 않는 한 기억은 유지됩니다.

### 2.2 가상환경 생성 및 실행
터미널(Anaconda Prompt 권장)을 열고 실행합니다.

```bash
# 가상환경 생성
conda env create -f environment.yml

# 가상환경 활성화
conda activate MACH_VII_v2.0

# 시스템 실행
python main.py
```
*   **정상 실행 확인**: 터미널에 `[Main] System Started` 로그가 출력되고, `http://localhost:8000` 접속 시 상태 메시지가 반환되어야 합니다.

---

## 3. 프론트엔드(Frontend) 환경 설정 및 실행

프론트엔드는 **React (Vite)** 기반입니다.

### 3.1 경로 이동 및 의존성 설치
```bash
cd embodiment/frontend

npm install
```

### 3.2 개발 서버 실행
```bash
npm run dev
```

### 3.3 웹 UI 접속
브라우저를 열고 `http://localhost:5173` 으로 접속합니다.
*   **정상 실행 확인**: 로봇 얼굴 UI가 표시되고, 백엔드와 WebSocket 연결이 성공했다는 로그가 콘솔(F12)에 찍혀야 합니다.

---

## 4. 트러블슈팅 (Troubleshooting)

### Q1. "ImportError: No module named ..." 오류가 발생합니다.
*   **해결**: `conda activate MACH_VII_v2.0`을 했는지 확인하세요. VS Code 인터프리터가 해당 Conda 환경을 바라보고 있는지 확인하세요.

### Q2. 웹소켓 연결이 자꾸 끊어집니다.
*   **해결**: 백엔드 서버(`main.py`)가 실행 중인지 확인하세요. 프론트엔드 코드의 `WEBSOCKET_URL` 설정이 `ws://localhost:8000/ws`로 되어 있는지 확인하세요.

### Q3. RealSense 카메라가 작동하지 않습니다.
*   **해결**: USB 3.0 포트에 연결되어 있는지 확인하세요. 만약 카메라가 없다면 시스템은 자동으로 **MOCK 모드(가상 시뮬레이션)**로 동작해야 합니다. 로그에 `Switching to MOCK mode`가 뜨는지 확인하세요.

---

## 5. 배포 (Deployment)

실제 운영 환경(로봇 PC)에 배포할 때는 Docker 대신 **Conda 환경 복제** 방식을 권장합니다.

1.  코드를 `git pull` 합니다.
2.  `conda env update --file environment.yml --prune` 으로 의존성을 동기화합니다.
3.  `python main.py`를 시작 프로그램으로 등록하거나 서비스로 실행합니다.
