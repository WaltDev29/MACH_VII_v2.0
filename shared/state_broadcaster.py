import threading
import time
from typing import Dict, Any, List, Callable

class StateBroadcaster:
    """
    LogicBrain이 상태를 발행하고 감정 시스템/UI가 이를 구독할 때 사용하는 싱글톤 브로드캐스터입니다.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StateBroadcaster, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self.latest_state = {
            "agent_state": "IDLE",     # PLANNING, EXECUTING, RECOVERING, IDLE
            "object_type": "none",     # 컵, 공 등
            "episode_result": "none",  # 성공(success), 실패(failure)
            "robot_status": "ok",      # 정상(ok), 오류(error)
            "chat_history": [],        # List of {"role": "bot", "text": "..."}
            "timestamp": time.time()
        }
    
    def log_chat(self, role: str, text: str):
        with self._lock:
            # 최근 20개까지만 기록 유지
            msg = {"role": role, "text": text, "timestamp": time.time()}
            history = self.latest_state.get("chat_history", [])
            history.append(msg)
            if len(history) > 20: history = history[-20:]
            self.latest_state["chat_history"] = history
            
            # 리스너 호출을 위해 스냅샷 복사
            snapshot = self.latest_state.copy()
        
        for sub in self.subscribers:
            try: sub(snapshot)
            except: pass

    def log_thought(self, text: str):
        """에이전트의 사고(Thought)를 기록합니다. UI에서는 챗 로그와 구분하여 표시할 수 있습니다."""
        # 현재는 챗 로그에 [사고] 태그로 넣어 같이 보여주거나 별도 리스트로 관리합니다.
        # 1차적으로는 챗 로그에 포함시키되 role='system' 또는 'thought'로 구분합니다.
        self.log_chat("thought", text)
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """상태 업데이트를 수신할 콜백 함수를 등록합니다."""
        with self._lock:
            self.subscribers.append(callback)
            
    def publish(self, key: str, value: Any):
        """특정 상태 키를 업데이트하고 구독자들에게 알립니다."""
        # thought(사고) 로그일 경우 별도로 기록 처리
        if key == "agent_thought":
             self.log_thought(str(value))

        with self._lock:
            self.latest_state[key] = value
            self.latest_state["timestamp"] = time.time()
            snapshot = self.latest_state.copy()
            
        # 구독자들에게 알림 (이상적으로는 비동기여야 하지만 MVP를 위해 단순 루프 사용)
        for sub in self.subscribers:
            try:
                sub(snapshot)
            except Exception as e:
                print(f"[Broadcaster] 구독자 오류: {e}")

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return self.latest_state.copy()

# 전역 인스턴스
broadcaster = StateBroadcaster()
