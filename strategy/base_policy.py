from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePolicy(ABC):
    """
    제어 정책을 위한 추상 인터페이스입니다.
    """
    
    @abstractmethod
    def execute_move(self, target_pos: Dict[str, float], context: Dict[str, Any]) -> bool:
        """
        정책에 따라 이동 명령을 수행합니다.
        
        Args:
            target_pos: {'x': float, 'y': float, 'z': float} (단위: cm)
            context: 환경 컨텍스트 (안전 제한, 객체 정보 등)
            
        Returns:
            bool: 성공 여부
        """
        pass

    @abstractmethod
    def execute_grasp(self, object_info: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        잡기(Grasp) 동작 시퀀스를 수행합니다.
        """
        pass
