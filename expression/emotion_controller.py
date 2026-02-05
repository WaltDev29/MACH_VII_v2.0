import threading
import time
import asyncio
import uuid
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
        self._lock = threading.RLock()
        
        # 우선순위 제어를 위한 타임스탬프 (파이프라인 업데이트 보호용)
        self.manual_override_until = 0.0
        
        self.last_preset_id = "neutral"
        self.muscles = {}
        
        # State Tracking
        self.current_brain_state = "IDLE"
        self.state_enter_time = time.time()
        
        # Heartbeat 타이머
        self.last_heartbeat_time = 0.0
        
        # 브레인 이벤트 구독
        broadcaster.subscribe(self.on_brain_state_change)

    def on_brain_state_change(self, state: Dict[str, any]):
        """브레인 상태가 변경될 때 호출되는 콜백입니다."""
        # 파이프라인에 의한 수동 조작이 활성화된 경우 상태 기반 자동 업데이트 무시
        if time.time() < self.manual_override_until:
            return

        agent_state = state.get("agent_state", "IDLE")
        
        with self._lock:
            # 상태 변경 시 초기화
            if agent_state != self.current_brain_state:
                self.current_brain_state = agent_state
                self.state_enter_time = time.time()
                print(f"[Emotion] Brain State Changed: {agent_state}")

            if agent_state == "PLANNING": # THINKING
                self.target_vector.focus = 0.8
                self.target_vector.effort = 0.3
                self.target_vector.curiosity = 0.7 
            elif agent_state == "EXECUTING":
                self.target_vector.focus = 1.0
                self.target_vector.effort = 0.6
                self.target_vector.confidence = 0.5
            elif agent_state == "IDLE":
                # [Refined] IDLE 초기에는 Neutral(평온) 유지
                # Bored(지루함) 조건(focus < 0.2)에 걸리지 않도록 안전값 설정
                self.target_vector.focus = 0.3
                self.target_vector.effort = 0.1
                self.target_vector.frustration = 0.0
                self.target_vector.confidence = 0.5 
                self.target_vector.curiosity = 0.3
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
                self.target_vector.curiosity = 0.5

    def update_target(self, new_target: Dict[str, float], duration: float = 3.0):
        """
        [Restored] 파이프라인/Updater에서 감정 벡터 목표를 조정할 때 호출.
        Vector System -> Pulse System으로의 다리 역할을 합니다.
        """
        with self._lock:
            self.manual_override_until = time.time() + duration
            for k, v in new_target.items():
                if hasattr(self.target_vector, k):
                    setattr(self.target_vector, k, v)

    def broadcast_emotion_event(self, preset_id: str, weight: float = 1.0, duration: float = 3.0):
        """
        [Emotion Pulse] 감정 사건(Event)을 발생시켜 프론트엔드로 브로드캐스트합니다.
        """
        print(f"[Emotion] Broadcasting Event: {preset_id} (w={weight:.2f}, d={duration}s)")
        
        # [Fix] 유실 방지 Event Buffer
        broadcaster.publish_event("emotion_pulse", {
            "preset": preset_id,
            "weight": weight,
            "duration": duration
        })

    def force_preset(self, preset_id: str):
        """
        [Legacy Support]
        """
        self.broadcast_emotion_event(preset_id, weight=1.0, duration=5.0)

    def step(self, dt: float):
        """현재 상태를 목표 상태로 보간하고 상태 유지를 위한 Heartbeat를 쏩니다."""
        smoothing_factor = 2.0 * dt # 속도 조절
        
        new_preset = "neutral"
        with self._lock:
            # [Advanced Logic] 시간에 따른 상태 변화 (Drift)
            self._apply_temporal_drift(dt)
            
            curr = self.current_vector
            tgt = self.target_vector
            
            # 1. 감정 벡터 보간 (Lerp)
            curr.focus += (tgt.focus - curr.focus) * smoothing_factor
            curr.effort += (tgt.effort - curr.effort) * smoothing_factor
            curr.confidence += (tgt.confidence - curr.confidence) * smoothing_factor
            curr.frustration += (tgt.frustration - curr.frustration) * smoothing_factor
            curr.curiosity += (tgt.curiosity - curr.curiosity) * smoothing_factor

            # 2. SystemState 동기화
            from state.system_state import system_state
            system_state.emotion.focus = curr.focus
            system_state.emotion.effort = curr.effort
            system_state.emotion.confidence = curr.confidence
            system_state.emotion.frustration = curr.frustration
            system_state.emotion.curiosity = curr.curiosity
            
            # 3. 프리셋 변경 감지 (락 내부에서는 계산만 수행)
            new_preset = self.get_closest_preset()
            
        # --- LOCK RELEASED ---
        
        # 3. 브로드캐스트 (락 밖에서 수행하여 콜백 데드락 방지)
        if new_preset != self.last_preset_id:
            print(f"[Emotion] Vector State Changed: {self.last_preset_id.upper()} -> {new_preset.upper()}")
            self.last_preset_id = new_preset
            if new_preset != 'neutral':
                 self.broadcast_emotion_event(new_preset, weight=1.0, duration=5.0)
                 
        # 4. [New] Heartbeat (락 밖에서 수행)
        if new_preset != 'neutral':
            now = time.time()
            if now - self.last_heartbeat_time > 0.5:
                # [Fix] 데드락 방지를 위해 publish_event를 락 밖에서 호출
                broadcaster.publish_event("emotion_pulse", {
                    "preset": new_preset,
                    "weight": 0.6,
                    "duration": 1.0
                })
                self.last_heartbeat_time = now

    def _apply_temporal_drift(self, dt: float):
        """시간 경과 및 배터리 상태에 따른 목표 벡터 자동 조정"""
        from state.system_state import system_state
        
        # 1. [Boredom Drift] IDLE 상태가 오래 지속되면 지루함으로 이동
        if self.current_brain_state == "IDLE":
             elapsed = time.time() - self.state_enter_time
             if elapsed > 10.0: # 10초 이상 대기 시
                 # Focus와 Effort를 서서히 낮춰서 Bored 조건(둘다 < 0.2) 충족 유도
                 self.target_vector.focus = max(0.05, self.target_vector.focus - 0.05 * dt)
                 self.target_vector.effort = max(0.0, self.target_vector.effort - 0.05 * dt)
                 


    def get_closest_preset(self) -> str:
        """
        현재 감정 벡터(6차원)를 기반으로 프론트엔드의 20가지 프리셋 중 가장 적절한 ID를 도출합니다.
        """
        vec = self.current_vector
        
        # 1. 극단적인 감정 상태 우선 확인 (High Intensity)
        if vec.frustration > 0.8: return "angry"     # 극심한 좌절 -> 분노
        if vec.confidence > 0.9: return "joy"        # 극심한 자신감 -> 환희
        if vec.focus > 0.9: return "focused"         # 극심한 집중 -> 집중
        
        # [Adjusted Threshold] 지루함 조건 강화 (IDLE 초기에는 안 걸리게)
        if vec.focus < 0.2 and vec.effort < 0.2: return "bored" 
        
        # 2. 복합 감정 상태 확인
        # [Priority Change] Thinking(Curiosity) 우선순위 상향
        # "Thinking 할 때는 무조건 Thinking 베이스여야 함"
        if vec.curiosity > 0.6:
            if vec.frustration > 0.4: return "confused" # 호기심 + 좌절(잘 안풀림) -> 혼란
            if vec.confidence > 0.5: return "excited"   # 호기심 + 자신감(잘 풀림) -> 흥분/신남
            return "thinking"                           # 순수 고민

        if vec.frustration > 0.4:
            if vec.effort > 0.5: return "pain"       # 좌절 + 노력(힘듦) -> 고통
            if vec.confidence < 0.3: return "sad"    # 좌절 + 낮은 자신감 -> 슬픔
            return "suspicious"                      # 단순 좌절 -> 의심/불만
            
        if vec.confidence > 0.6:
            if vec.focus > 0.6: return "proud"       # 자신감 + 집중 -> 자부심
            return "happy"                           # 단순 자신감 -> 기쁨
             
        if vec.focus > 0.6:
             return "focused"                         # 단순 집중
             
        if vec.effort > 0.7:
             return "tired"                           # 높은 노력 -> 피곤함

        # 3. 기본 상태
        return "neutral"

    def _check_preset_change(self):
        """감정 프리셋이 변경되었는지 확인하고 이벤트를 발생시킵니다."""
        new_preset = self.get_closest_preset()
        
        if new_preset != self.last_preset_id:
            # 상태 변경 시에는 강한 펄스 전송
            vec = self.current_vector
            print(f"[Emotion] Vector State Changed: {self.last_preset_id.upper()} -> {new_preset.upper()}")
            
            self.last_preset_id = new_preset
            
            if new_preset != 'neutral':
                 self.broadcast_emotion_event(new_preset, weight=1.0, duration=5.0)

    def start(self):
        """60Hz 보간 루프를 시작합니다."""
        if self.running: return
        self.running = True
        self.muscles = {} 
        self.last_preset_id = "neutral" 
        self.current_brain_state = "IDLE" # 초기화
        self.state_enter_time = time.time()
        
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
            preset = self.get_closest_preset()
            return {
                "vector": self.current_vector.to_dict(),
                "preset_id": preset,
                "muscles": {}
            }

# 싱글톤 인스턴스
emotion_controller = EmotionController()
