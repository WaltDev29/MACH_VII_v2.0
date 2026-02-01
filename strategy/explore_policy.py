import random
from typing import Dict, Any
from .base_policy import BasePolicy
from .safe_policy import SafePolicy

class ExplorePolicy(SafePolicy):
    """
    탐험 정책(Exploration Policy): 접근 각도와 속도에 노이즈를 추가하여 데이터를 수집합니다.
    SafePolicy의 안정성을 상속받지만 파라미터를 재정의합니다.
    """
    
    def execute_move(self, target_pos: Dict[str, float], context: Dict[str, Any]) -> bool:
        # 데이터 수집을 위해 목표 위치에 약간의 가우시안 노이즈 추가 (안전한 경우)
        noise_x = random.uniform(-0.5, 0.5) # +/- 0.5cm
        noise_y = random.uniform(-0.5, 0.5)
        
        adjusted_target = target_pos.copy()
        adjusted_target['x'] += noise_x
        adjusted_target['y'] += noise_y
        
        print(f"[ExplorePolicy] Moving to {adjusted_target} (Noise Added) with Speed=MEDIUM")
        # 약간 더 높은 속도나 변화를 주며 실행
        return True

    def execute_grasp(self, object_info: Dict[str, Any], context: Dict[str, Any]) -> bool:
        approach_angle = random.choice([0, 15, -15]) # 다양한 손목 각도 시도
        print(f"[ExplorePolicy] Grasping with approach_angle={approach_angle} deg")
        return True
