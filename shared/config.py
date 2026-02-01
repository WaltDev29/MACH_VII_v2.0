import os
from pathlib import Path
from dotenv import load_dotenv

class GlobalConfig:
    """시스템 전역 설정 클래스입니다."""
    SIM_MODE = True
    
    # 브레인(Brain) 설정
    VLM_ENDPOINT = "http://ollama.aikopo.net/api/generate"
    VLM_MODEL = "gemma3:27b"
    
    # 통신 및 서버 설정
    SIM_SERVER_URL = "http://localhost:5000"
    API_PORT = 8000
    
    # 감정(Emotion) 설정
    EMOTION_UPDATE_INTERVAL = 0.5  # 초 단위 (저수준 LLM 업데이트 주기)
    EMOTION_RENDER_FPS = 60        # 초당 프레임 수 (고수준 보간 루프)
    
    # 로봇(Robot) 및 센서(Sensor) 설정
    ROBOT_IP = "192.168.0.100"     # DOFBOT IP 주소
    CAMERA_FPS = 30

class CameraConfig:
    """카메라 설치 위치 및 오프셋 설정 클래스입니다."""
    # 시뮬레이션 환경 (PyBullet) 오프셋
    # PyBullet 카메라 위치: cameraEyePosition=[0.5, 0, 0.5] (m 단위)
    # → cm 단위로 변환: X=50cm, Y=0cm, Z=50cm
    SIM_OFFSET = {"x": 50.0, "y": 0.0, "z": 50.0}  # cm 단위
    
    # 실물 환경 (Intel RealSense) 오프셋
    REAL_OFFSET = {"x": 30.0, "y": 0.0, "z": 20.0}
    
class PathConfig:
    """pathlib을 사용한 경로 관리 클래스입니다."""
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
load_dotenv(PathConfig.BASE_DIR / ".env")
PathConfig.ensure_dirs()