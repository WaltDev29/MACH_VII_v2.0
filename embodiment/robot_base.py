from abc import ABC, abstractmethod
from typing import List, Dict, Any

class RobotBase(ABC):
    """
    로봇 제어를 위한 최상위 공통 인터페이스 규격입니다.
    URDF 설계도에 명시된 5축 팔과 그리퍼 구조를 따릅니다.
    모든 길이는 cm, 모든 각도는 도(Degree) 단위를 사용합니다.
    오른손 좌표계(Right-Hand Rule) 규격을 준수합니다.
    """

    def __init__(self):
        """
        로봇의 현재 상태 정보를 관리하는 변수들을 초기화합니다.
        """
        # 로봇의 현재 상태를 저장하는 딕셔너리입니다.
        self.current_state = {
            # 현재 끝단(End-Effector)의 위치 (단위: cm)
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            
            # URDF에 정의된 5개의 회전 관절 각도입니다.
            # joint1, joint2, joint3, joint4, joint5 순서입니다.
            "joints": [0.0] * 5,
            
            # 그리퍼의 상태입니다. (0: 완전히 닫힘, 100: 3cm 열림)
            "gripper": 0.0,
            
            # 로봇이 현재 동작 중인지 나타내는 상태 값입니다.
            "is_moving": False
        }

    @abstractmethod
    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """
        목표 좌표(x, y, z)로 로봇 끝단을 이동시킵니다.
        입력된 cm 좌표는 각 담당자(PyBullet/DOFBOT)가 내부적으로 처리합니다.
        
        Args:
            x, y, z: 목표 좌표 (단위: cm)
            speed: 이동 속도 (0 ~ 100)
        Returns:
            bool: 이동 성공 여부
        """
        pass

    @abstractmethod
    def set_joints(self, angles: List[float], speed: int = 50) -> bool:
        """
        5개 관절의 각도를 직접 제어합니다.
        
        Args:
            angles: 5개 관절의 목표 각도 리스트 (단위: 도)
            speed: 이동 속도 (0 ~ 100)
        """
        pass

    @abstractmethod
    def move_gripper(self, open_percent: float) -> bool:
        """
        그리퍼의 개폐를 제어합니다.
        0%는 0m(닫힘), 100%는 0.03m(3cm 열림)에 매핑됩니다.
        
        Args:
            open_percent: 그리퍼 개방 정도 (0 ~ 100)
        """
        pass

    @abstractmethod
    def get_current_pose(self) -> Dict[str, Any]:
        """
        로봇의 현재 좌표, 관절 각도, 그리퍼 상태를 반환합니다.
        """
        pass

    @abstractmethod
    def emergency_stop(self):
        """
        위급 상황 시 로봇의 모든 구동을 즉시 중단합니다.
        """
        pass