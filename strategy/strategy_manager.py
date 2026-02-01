# strategy/strategy_manager.py

import threading
from typing import Dict, Any

class StrategyManager:
    """
    시스템의 전역 전략(Layer 4)을 관리하는 싱글톤 매니저입니다.
    성향, 위험 수위, 탐험 허용 여부 등 에이전트의 행동 방침을 결정합니다.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StrategyManager, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        # 기본 전략 설정
        self.context = {
            "allow_explore": False,     # 탐험 모드 활성화 여부
            "risk_level": "LOW",        # 위험 감수 수준 (LOW, MEDIUM, HIGH)
            "persona": "CAUTIOUS"       # 페르소나 (CAUTIOUS, AGGRESSIVE, FRIENDLY)
        }

    def set_context(self, allow_explore: bool = None, risk_level: str = None, persona: str = None):
        """본체의 전략적 맥락을 업데이트합니다."""
        with self._lock:
            if allow_explore is not None:
                self.context["allow_explore"] = allow_explore
            if risk_level is not None:
                self.context["risk_level"] = risk_level
            if persona is not None:
                self.context["persona"] = persona
        
        print(f"[Strategy] 컨텍스트 업데이트: {self.context}")

    def set_mode(self, mode: str):
        """사고 방식(Operation Mode)을 전환합니다."""
        from shared.ui_dto import OperationMode
        self.context["op_mode"] = mode
        print(f"[Strategy] 사고 모드 전환 완료: {mode}")

    def get_context(self) -> Dict[str, Any]:
        """현재 적용 중인 전략적 맥락을 반환합니다."""
        with self._lock:
            return self.context.copy()

    def filter_action(self, intent: str) -> bool:
        """
        [핵심] 브레인의 의도(Intent)가 현재 전략에 부합하는지 필터링합니다.
        위험 수위나 탐험 설정에 따라 특정 행동을 차단하거나 승인합니다.
        """
        context = self.get_context()
        intent_low = intent.lower()

        # 예: 위험 수위가 LOW인데 위험한 행동(전투 등)을 하려 할 경우 필터링
        if context["risk_level"] == "LOW":
            if any(word in intent_low for word in ["공격", "attack", "fight"]):
                print(f"[Strategy] 차단됨: 위험 수위(LOW)에서 위험 행동 감지 -> {intent}")
                return False

        # 예: 탐험이 금지되었는데 새로운 지역으로 가려 할 경우
        if not context["allow_explore"]:
            if any(word in intent_low for word in ["탐험", "explore", "search"]):
                print(f"[Strategy] 차단됨: 탐험 비활성화 상태에서 탐험 시도 -> {intent}")
                return False

        return True

# 싱글톤 인스턴스
strategy_manager = StrategyManager()
