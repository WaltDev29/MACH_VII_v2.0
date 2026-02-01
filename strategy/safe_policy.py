import time
from typing import Dict, Any
from .base_policy import BasePolicy
# 실제 시나리오에서는 Core/Robot 인터페이스를 가져옵니다.
# from core.robot_base import RobotBase

class SafePolicy(BasePolicy):
    """
    보수적인 정책(Consistent Policy): 선형 보간, 낮은 속도, 엄격한 안전 검사를 수행합니다.
    """
    def __init__(self, robot_interface=None):
        self.robot = robot_interface # 의존성 주입 (Dependency Injection)

    def execute_move(self, target_pos: Dict[str, float], context: Dict[str, Any]) -> bool:
        print(f"[SafePolicy] {target_pos}로 이동합니다 (속도=LOW)")
        # 로직:
        # 1. 작업 공간(Workspace) 내 목표 위치 유효성 검사
        # 2. 속도 30%로 선형(Cartesian) 이동
        # 3. 말단 장치(End-Effector) 도달 확인
        return True

    def execute_grasp(self, object_info: Dict[str, Any], context: Dict[str, Any]) -> bool:
        print(f"[SafePolicy] {object_info.get('name')} 잡기를 시도합니다 (수직 접근)")
        # 로직:
        # 1. Z+10cm 위치에서 접근
        # 2. 천천히 하강
        # 3. 그리퍼 닫기
        # 4. 수직으로 들어올리기
        return True
