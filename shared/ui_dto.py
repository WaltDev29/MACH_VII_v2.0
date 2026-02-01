from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional

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
    PHYSICAL = "dofbot"              # 실물 Dofbot 암 (Serial/Jetson 기반 제어)

# 3. 카메라 소스 선택 (Sensor Layer)
class CameraSource(str, Enum):
    """시스템의 시각 지각(Perception)을 위한 영상 입력 소스를 결정합니다."""
    VIRTUAL = "pybullet"             # 시뮬레이터 내부의 가상 카메라
    REAL = "realsense"               # Intel RealSense 실제 뎁스 카메라

# 4. 사고 방식 설정 (Brain/Logic Layer)
class OperationMode(str, Enum):
    """맹칠이의 사고 및 의도 결정 프로세스를 정의합니다. (7 Layer - Layer 3 담당)"""
    
    RULE_BASED = "rule_based"        
    # [설명] 사전 정의된 IF-THEN 로직이나 하드코딩된 시나리오에 따라 동작합니다.
    # 결정론적으로 움직여야 할 때나 초기 셋업 시 유용합니다.
    
    MEMORY_BASED = "memory_based"    
    # [설명] 과거 결정 데이터(FalkorDB)와 현재 상황을 VLM(LLM)이 대조하여 판단합니다.
    # 예기치 못한 상황 대응이나 능동적인 문제 해결 시 사용됩니다.

# 5. 시스템 하부 구조 설정을 위한 DTO
class SystemConfigurationDTO(BaseModel):
    """인프라 및 알고리즘 동작 방식을 결정하는 세부 설정 묶음입니다."""
    
    target_robot: RobotTarget = Field(..., description="제어 대상 로봇 장치 선택")
    active_camera: CameraSource = Field(..., description="지각 시스템용 카메라 소스 선택")
    op_mode: OperationMode = Field(..., description="맹칠이의 판단 엔진 모드 설정")
    is_emergency_stop: bool = Field(False, description="긴급 정지 상태 여부 (True 시 모든 Embodiment 동작 정지)")

# 6. 최종 통합 요청 DTO (Perfect Interface)
class UserRequestDTO(BaseModel):
    """
    UI에서 서버(Brain/API)로 전달되는 유일한 규격화된 메시지 패킷입니다.
    Strict Interface 원칙에 따라 모든 레이어 진입 시 이 형식을 따릅니다.
    """
    
    request_type: UserRequestType = Field(..., description="요청의 성격 (COMMAND/CONFIG_CHANGE/EMERGENCY)")
    
    # 사용자의 자연어 명령 (request_type == COMMAND 일 때 주로 사용)
    command: Optional[str] = Field(None, description="텍스트 기반 고수준 사용자 명령")
    
    # 시스템 설정 변경 세부 사항 (request_type == CONFIG_CHANGE 일 때 포함)
    config: Optional[SystemConfigurationDTO] = Field(None, description="변경하고자 하는 시스템 설정 상세")

    class Config:
        """Pydantic 설정: JSON 직렬화 시 Enum 값을 문자열로 변환하여 호환성 유지"""
        use_enum_values = True
