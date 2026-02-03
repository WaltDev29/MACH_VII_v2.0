from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict, Any

# 1. 요청 성격 구분을 위한 열거형 (Request Dispatching)
class UserRequestType(str, Enum):
    """사용자가 UI를 통해 전달하는 요청의 종류를 정의합니다."""
    COMMAND = "command"              # 텍스트 명령 (예: "저 물건 가져와")
    CONFIG_CHANGE = "config_change"  # 설정 변경 (로봇/카메라 소스 등)
    EMERGENCY = "emergency"          # 긴급 정지 (즉시 제어 중단 및 안전 확보)

# 2. 로봇 대상 선택 (Embodiment Layer)
class RobotTarget(str, Enum):
    """제어 명령이 최종적으로 전달될 물리/가상 하드웨어를 선택합니다."""
    VIRTUAL = "pybullet"             # PyBullet 시뮬레이터 내 가상 로봇
    PHYSICAL = "dofbot"              # 실물 Dofbot 팔 (Serial/Jetson 기반 제어)

# 3. 카메라 소스 선택 (Sensor Layer)
class CameraSource(str, Enum):
    """시스템의 시각 지각(Perception)을 위한 영상 입력 소스를 결정합니다."""
    VIRTUAL = "pybullet"             # 시뮬레이터 내부의 가상 카메라
    REAL = "realsense"               # Intel RealSense 실제 뎁스 카메라

# 4. 사고 방식 설정 (Brain/Logic Layer)
class OperationMode(str, Enum):
    """맹칠이의 사고 및 의도 결정 프로세스를 정의합니다. (7 Layer - Layer 3 담당)"""
    
    RULE_BASED = "rule_based" # 안전 모드       
    # 사전 정의된 로직이나 하드코딩된 시나리오에 따라 동작합니다.
    
    MEMORY_BASED = "memory_based" # 리드미상 탐험모드 -> Exploitation (활용) 모드 로 개선 예정    
    # FalkorDB 데이터와 현재 상황을 비교하여 판단

    # MEMORY_BASED = "thinking_based" # 추후 추가할 진짜 탐험모드 FalkorDB 참고로 삼아 진짜 사고하는 llm 기반

# 5. 시스템 하부 구조 설정을 위한 DTO
class SystemConfigurationDTO(BaseModel):
    """인프라 및 알고리즘 동작 방식을 결정하는 세부 설정 묶음입니다."""
    
    target_robot: RobotTarget = Field(..., description="제어 대상 로봇 장치 선택")
    active_camera: CameraSource = Field(..., description="지각 시스템용 카메라 소스 선택")
    op_mode: OperationMode = Field(..., description="맹칠이의 판단 엔진 모드 설정")
    is_emergency_stop: bool = Field(False, description="긴급 정지 상태 여부 (True 시 모든 Embodiment 동작 정지)")

# 6. 최종 통합 요청 DTO
class UserRequestDTO(BaseModel):
    """
    UI에서 서버(Brain/API)로 전달되는 유일한 규격화된 메시지 패킷입니다.
    전송 통일성을 위해 모든 레이어 진입 시 이 형식을 따라야 합니다.
    """
    
    request_type: UserRequestType = Field(..., description="요청의 성격 (COMMAND/CONFIG_CHANGE/EMERGENCY)")
    
    # 사용자의 자연어 명령 (request_type == COMMAND 일 때 주로 사용)
    command: Optional[str] = Field(None, description="텍스트 기반 고수준 사용자 명령")
    
    # 시스템 설정 변경 세부 사항 (request_type == CONFIG_CHANGE 일 때 포함)
    config: Optional[SystemConfigurationDTO] = Field(None, description="변경하고자 하는 시스템 설정 상세")

    class Config:
        """Pydantic 설정: JSON 직렬화 시 Enum 값을 문자열로 변환하여 호환성 유지"""
        use_enum_values = True
    # 왜 Enum 값을 문자열로 변환해야 하냐면, JSON과 UI는 문자열로 변환된 데이터만을 처리할 수 있고, 내부 로직을 변경해도 데이터 통일성을 유지할 수 있기 때문

# 7. 감정 상태 데이터 (Phase 2 추가)
class EmotionData(BaseModel):
    """
    백엔드(Brain)에서 분석된 감정 상태를 프론트엔드로 전달하기 위한 데이터셋입니다.
    벡터 값과 함께, UI가 즉시 렌더링할 수 있는 '프리셋 ID'를 포함합니다.
    """
    vector: Dict[str, float] = Field(..., description="Focus, Confidence 등 6차원 감정 벡터")
    preset_id: str = Field(..., description="프론트엔드 FaceContext가 사용할 표정 프리셋 ID (예: happy, angry)")
    muscles: Optional[Dict[str, Any]] = Field({}, description="눈, 입 등의 저수준 미세 제어 파라미터 (선택 사항)")

# 8. 시스템 전체 스냅샷 (Phase 2 추가 - WebSocket 패킷 규격)
class SystemSnapshot(BaseModel):
    """
    WebSocket(/ws)을 통해 프론트엔드로 실시간 전송되는 시스템의 전체 상태입니다.
    7-Layer 아키텍처의 각 구성 요소 상태를 모두 포함하여 정합성을 보장합니다.
    """
    timestamp: float = Field(..., description="스냅샷 생성 시간 (Unix Timestamp)")
    
    # 각 레이어별 상태 데이터
    brain: Dict[str, Any] = Field(..., description="[Layer 3] LogicBrain 상태 (현재 생각, 작업 상태 등)")
    emotion: EmotionData = Field(..., description="[Layer 5] 현재 감정 상태 및 표정 프리셋")
    perception: Dict[str, Any] = Field(..., description="[Layer 1] 인식된 객체 및 센서 데이터")
    
    # 로봇 상태 (간소화)
    robot: Dict[str, Any] = Field(..., description="[Layer 6] 로봇의 물리적 상태 (배터리, 모드, 이동 여부)")
    
    # 전략 컨텍스트
    strategy: Dict[str, Any] = Field(..., description="[Layer 4] 현재 전략 모드 및 판단 근거")
    
    # 시각화 데이터
    last_frame: Optional[str] = Field(None, description="[Layer 1] Base64로 인코딩된 실시간 카메라 프레임")
