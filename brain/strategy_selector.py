from typing import Dict, Any
from strategy.safe_policy import SafePolicy
from strategy.explore_policy import ExplorePolicy
from memory.falkordb_manager import memory_manager
import logging

class StrategySelector:
    """
    안전성(System Safety), 신뢰도(Confidence), 그리고 UI 설정을 기반으로 적절한 정책을 선택합니다.
    """
    def __init__(self):
        self.safe_policy = SafePolicy()
        self.explore_policy = ExplorePolicy()

    def select_policy(self, context: Dict[str, Any], task_command: str = None):
        """
        정책을 선택합니다.
        
        선택 로직:
        - UI 탐험 허용(Explore Allowed)이 False인 경우 -> 안전(Safe) 모드
        - 위험 레벨(Risk Level)이 높음(HIGH)인 경우 -> 안전(Safe) 모드
        - 메모리상 성공률이 임계값 미만인 경우 -> 안전(Safe) 모드 (실패로부터 학습)
        """
        
        allow_explore = context.get("allow_explore", False)
        risk_level = context.get("risk_level", "LOW")
        
        # 1. 메모리 확인 (읽기 경로)
        if task_command:
            success_rate = memory_manager.get_recent_success_rate(target=task_command)
            logging.info(f"[Strategy] Memory check for '{task_command}': Success Rate = {success_rate:.2f}")
            
            # 실패가 너무 잦은 경우 (예: < 0.4), 탐험이 허용되어도 강제로 안전 모드로 전환
            if success_rate < 0.4:
                logging.warning(f"[Strategy] Memory Override: Success rate low. Forcing SafePolicy.")
                return self.safe_policy
        
        # 2. 기본 로직
        if allow_explore and risk_level == "LOW":
            return self.explore_policy
        
        return self.safe_policy
