from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .emotion_state import EmotionVector

@dataclass
class RobotStatus:
    is_moving: bool = False
    battery_level: float = 100.0
    current_mode: str = "IDLE"

@dataclass
class SystemState:
    """
    시스템의 전체 상태를 정의하는 '단일 진실 공급원(Single Source of Truth)'입니다.
    
    이 클래스의 인스턴스(system_state)는 프로그램 전체에서 유일하게 하나만 존재하며(싱글톤),
    모든 모듈(Brain, Expression, Robot 등)은 이 객체를 참조하여 현재 로봇의 상황을 파악합니다.
    """
    # 하위 상태 컴포넌트들
    emotion: EmotionVector = field(default_factory=EmotionVector)
    robot: RobotStatus = field(default_factory=RobotStatus)
    
    # 센서 데이터 (Raw Data가 아닌 가공된 정보)
    perception_data: Dict[str, Any] = field(default_factory=dict)
    
    # VLM 분석을 위한 최신 프레임 (Base64 Encoded JPEG)
    last_frame_base64: Optional[str] = None
    
    # 현재 활성화된 Intent (Brain이 결정한 의도)
    current_intent: str = "IDLE"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion.to_dict(),
            "robot": {
                "is_moving": self.robot.is_moving,
                "battery": self.robot.battery_level,
                "mode": self.robot.current_mode
            },
            "perception": self.perception_data,
            "intent": self.current_intent
        }

# 전역 상태 인스턴스 (메모리상 유일)
system_state = SystemState()
