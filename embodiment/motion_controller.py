# embodiment/motion_controller.py

import numpy as np

class MotionController:
    """
    현재 위치와 목표 위치를 비교하여 정밀 이동 전략을 수립합니다.
    """
    def __init__(self, precision_threshold_cm: float = 3.0):
        # 정밀 제어 모드가 활성화되는 거리 기준입니다.
        self.precision_threshold = precision_threshold_cm

    def calculate_distance(self, pos1: dict, pos2: dict) -> float:
        """두 3D 좌표 사이의 유클리드 거리를 cm 단위로 계산합니다."""
        p1 = np.array([pos1['x'], pos1['y'], pos1['z']])
        p2 = np.array([pos2['x'], pos2['y'], pos2['z']])
        return np.linalg.norm(p1 - p2)

    def get_strategy(self, current_pose: dict, target_pose: dict) -> dict:
        """
        목표와의 거리를 측정하여 이동 속도와 정밀 제어 여부를 결정합니다.
        """
        distance = self.calculate_distance(current_pose, target_pose)
        
        # 3cm 이내인 경우: 속도를 낮추고 정밀 모드로 진입합니다.
        if distance <= self.precision_threshold:
            return {
                "speed": 15, 
                "is_precision": True, 
                "distance": distance,
                "msg": "정밀 접근 모드 활성화"
            }
        
        # 먼 거리인 경우: 빠른 속도로 일반 이동을 수행합니다.
        return {
            "speed": 80, 
            "is_precision": False, 
            "distance": distance,
            "msg": "일반 이동 모드 수행"
        }