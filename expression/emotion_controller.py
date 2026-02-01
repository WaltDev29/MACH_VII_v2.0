import threading
import time
import asyncio
from typing import Dict
from state.emotion_state import EmotionVector
from shared.state_broadcaster import broadcaster

class EmotionController:
    """
    현재 감정 벡터를 목표 벡터로 부드럽게 보간(Interpolate)하는 고속 컨트롤러입니다.
    StateBroadcaster를 구독하여 주요 상태 변화에 반응합니다.
    """
    def __init__(self):
        self.current_vector = EmotionVector()
        self.target_vector = EmotionVector()
        self.running = False
        self._lock = threading.Lock()
        
        # 우선순위 제어를 위한 타임스탬프 (파이프라인 업데이트 보호용)
        self.manual_override_until = 0.0
        
        # 브레인 이벤트 구독
        broadcaster.subscribe(self.on_brain_state_change)

    def on_brain_state_change(self, state: Dict[str, any]):
        """브레인 상태가 변경될 때 호출되는 콜백입니다."""
        # 파이프라인에 의한 수동 조작이 활성화된 경우 상태 기반 자동 업데이트 무시
        if time.time() < self.manual_override_until:
            return

        agent_state = state.get("agent_state", "IDLE")
        
        with self._lock:
            if agent_state == "PLANNING":
                self.target_vector.focus = 0.8
                self.target_vector.effort = 0.3
            elif agent_state == "EXECUTING":
                self.target_vector.focus = 1.0
                self.target_vector.effort = 0.6
            elif agent_state == "IDLE":
                self.target_vector.focus = 0.3
                self.target_vector.effort = 0.0
                self.target_vector.frustration = 0.0
                self.target_vector.confidence = 0.5 
            elif agent_state == "RECOVERING": 
                self.target_vector.focus = 0.5
                self.target_vector.frustration = 0.9 
                self.target_vector.confidence = 0.1
                self.target_vector.effort = 0.8
            elif agent_state == "SUCCESS":
                self.target_vector.focus = 0.5
                self.target_vector.frustration = 0.0
                self.target_vector.confidence = 1.0 
                self.target_vector.effort = 0.0

    def update_target(self, new_target: Dict[str, float], duration: float = 3.0):
        """
        파이프라인 등에서 감정 목표를 명시적으로 조정할 때 호출합니다. 
        일정 시간(duration) 동안 상태 기반 자동 업데이트를 차단합니다.
        """
        with self._lock:
            self.manual_override_until = time.time() + duration
            for k, v in new_target.items():
                if hasattr(self.target_vector, k):
                    setattr(self.target_vector, k, v)

    def step(self, dt: float):
        """현재 상태를 목표 상태로 보간하고, 물리 표현 파라미터(Muscles)를 계산합니다."""
        smoothing_factor = 2.0 * dt # 속도 조절
        
        with self._lock:
            curr = self.current_vector
            tgt = self.target_vector
            
            # 1. 감정 벡터 보간 (Lerp)
            curr.focus += (tgt.focus - curr.focus) * smoothing_factor
            curr.effort += (tgt.effort - curr.effort) * smoothing_factor
            curr.confidence += (tgt.confidence - curr.confidence) * smoothing_factor
            curr.frustration += (tgt.frustration - curr.frustration) * smoothing_factor
            curr.curiosity += (tgt.curiosity - curr.curiosity) * smoothing_factor

            # 2. [NEW] 물리 표현 파라미터 계산 (Dumb UI 지원)
            # 프론트엔드가 복잡한 계산을 하지 않도록 최종 렌더링 값(0~1)을 산출합니다.
            self.muscles = {
                "eye": {
                    # Effort(노력)가 클수록 눈을 가늘게 뜸 (집중/피로)
                    "openness": float(max(0.0, min(1.0, 1.0 - (curr.effort * 0.3)))),
                    # Confidence(자신감)가 높으면 미소, Frustration(좌절)이 높으면 찡그림
                    "smile": float(max(-1.0, min(1.0, (curr.confidence * 1.0) - (curr.frustration * 1.0)))),
                },
                "mouth": {
                    # 입꼬리: 자신감 vs 좌절 경쟁
                    "smile": float(max(-1.0, min(1.0, (curr.confidence * 1.0) - (curr.frustration * 1.0)))),
                    # 자신감이 넘치면 입을 더 크게 벌림 (당당함)
                    "width": float(max(0.0, min(1.0, 0.5 + (curr.confidence * 0.3))))
                },
                "head": {
                    # Curiosity(호기심)가 높으면 고개를 갸웃거림 (Roll 회전)
                    "roll": float(max(-20.0, min(20.0, curr.curiosity * 15.0 if curr.curiosity > 0.6 else 0.0)))
                }
            }

    def start(self):
        """60Hz 보간 루프를 시작합니다."""
        if self.running: return
        self.running = True
        self.muscles = {} # 파라미터 초기화
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        print("[Emotion] 컨트롤러 시작됨 (60Hz).")

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)
            
    def _loop(self):
        last_time = time.time()
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            self.step(dt)
            
            # 약 60Hz 유지
            time.sleep(max(0, 1/60.0 - (time.time() - current_time)))

    def get_current_emotion(self):
        with self._lock:
            return {
                "vector": self.current_vector.to_dict(),
                "muscles": self.muscles
            }

# 싱글톤 인스턴스
emotion_controller = EmotionController()
