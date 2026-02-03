import os
from pathlib import Path
from dotenv import load_dotenv # 환경 변수 로드용

class GlobalConfig:
    """시스템 전역 설정 클래스입니다."""
    SIM_MODE = True # 현재 시스템이 시뮬레이션(PyBullet) 모드인지, 실제 로봇 모드인지 결정하는 스위치
    
    # 브레인(Brain) 설정
    VLM_ENDPOINT = "http://ollama.aikopo.net/api/generate" # 엔드포인트를 통해 호출할 모델 주소
    VLM_MODEL = "gemma3:27b" # 엔드포인트를 통해 호출할 모델 이름
    
    # 통신 및 서버 설정
    SIM_SERVER_URL = "http://localhost:5000" # 시뮬레이션 서버 URL
    API_PORT = 8000 # API 서버 포트
    
    # 감정(Emotion) 설정
    EMOTION_UPDATE_INTERVAL = 0.5  # 초 단위 (저수준 LLM 업데이트 주기)
    EMOTION_RENDER_FPS = 60        # 초당 프레임 수 (고수준 보간 루프로 60fps)
    
    # 로봇(Robot) 및 센서(Sensor) 설정
    ROBOT_IP = "192.168.0.100"     # DOFBOT IP 주소 (과거 종민이랑 연결했던 IP 기반)
    CAMERA_FPS = 30 # 카메라 FPS 

class CameraConfig:
    """카메라 설치 위치 및 오프셋 설정 클래스입니다."""
    # 시뮬레이션 환경 (PyBullet) 오프셋
    # PyBullet 카메라 위치: cameraEyePosition=[0.5, 0, 0.5] (m 단위)
    # → cm 단위로 변환: X=50cm, Y=0cm, Z=50cm
    SIM_OFFSET = {"x": 50.0, "y": 0.0, "z": 50.0}  # cm 단위
    
    # 실물 환경 (Intel RealSense) 오프셋 
    REAL_OFFSET = {"x": 30.0, "y": 0.0, "z": 20.0} #(일단 지금 사용 안해서 아무렇게나 잡아둠)
    
class PathConfig:
    """pathlib을 사용한 경로 관리 클래스입니다."""
    # pathlib 사용 이유는, 전역 관리가 쉽기 때문 (하드코딩 방지)
   
    # __file__ : 현재 파일의 경로를 나타냄
    # resolve() : 상대 경로를 절대 경로로 변환
    # parent : 상위 디렉토리
    # parent.parent : 상위 디렉토리의 상위 디렉토리
    # / : pathlib의 경로 연결 연산자
    # mkdir() : 디렉토리 생성
    # parents=True : 상위 디렉토리가 없으면 생성
    # exist_ok=True : 디렉토리가 이미 있으면 무시
    # ensure_dirs() : 필요 디렉토리가 없으면 생성

    # BASE_DIR : 프로젝트의 최상위 디렉토리
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # 7 Layer Pipeline 및 주요 디렉토리
    SENSOR_DIR = BASE_DIR / "sensor"
    STATE_DIR = BASE_DIR / "state"
    BRAIN_DIR = BASE_DIR / "brain"
    STRATEGY_DIR = BASE_DIR / "strategy"
    EXPRESSION_DIR = BASE_DIR / "expression"
    EMBODIMENT_DIR = BASE_DIR / "embodiment"
    MEMORY_DIR = BASE_DIR / "memory"
    
    # 공유 및 인터페이스
    SHARED_DIR = BASE_DIR / "shared"
    INTERFACE_DIR = BASE_DIR / "interface"
    
    # 데이터 및 문서
    DATA_DIR = BASE_DIR / "data"
    MODEL_DIR = DATA_DIR / "models"
    LOG_DIR = DATA_DIR / "logs"
    DOCS_DIR = BASE_DIR / "docs"

    @staticmethod
    def ensure_dirs():
        """필요한 데이터 디렉토리가 없으면 생성합니다."""
        for path in [PathConfig.DATA_DIR, PathConfig.MODEL_DIR, PathConfig.LOG_DIR]:
            path.mkdir(parents=True, exist_ok=True)

# 환경 변수 로드 
# .env 파일에서 환경 변수를 로드할 수도 있으니까 미리 만들어둠. (.env.example로 만들어둠 내용은 없음)
load_dotenv(PathConfig.BASE_DIR / ".env")
PathConfig.ensure_dirs()