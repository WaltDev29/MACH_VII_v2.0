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

            # 2. [Phase 2] 물리 표현 파라미터 계산 비활성화 (Preset Priority)
            # 프론트엔드의 정교한 프리셋(Bezier Curve 등)이 백엔드의 단순 수식보다 훨씬 고품질이므로,
            # 백엔드는 이제 '어떤 프리셋을 쓸지(States)'만 결정하고, 세부 근육 제어는 하지 않습니다.
            # 만약 백엔드가 muscles 값을 보내면 프론트엔드가 이를 덮어써서 표정이 '망가질(Mangle)' 위험이 있습니다.
            
            # self.muscles = { ... } # DEPRECATED: Legacy Dumb UI Logic
            self.muscles = {} 

            
            # 3. [Phase 2] 전역 SystemState 동기화 (Single Source of Truth 준수)
            # Brain 등 다른 레이어가 최신 감정 상태를 알 수 있도록 system_state.emotion을 업데이트합니다.
            from state.system_state import system_state
            
            # 벡터 값 복사 (Deep Copy or Field Copy)
            # lock 내부이므로 안전하게 복사
            system_state.emotion.focus = curr.focus
            system_state.emotion.effort = curr.effort
            system_state.emotion.confidence = curr.confidence
            system_state.emotion.frustration = curr.frustration
            system_state.emotion.curiosity = curr.curiosity
            
            # [Phase 2] 프리셋 변경 감지 및 로깅
            self._check_preset_change()

    def get_closest_preset(self) -> str:
        """
        현재 감정 벡터(6차원)를 기반으로 프론트엔드의 20가지 프리셋 중 가장 적절한 ID를 도출합니다.
        단순 임계값(Threshold) 로직을 사용하여 계산 비용을 최소화합니다.
        """
        # Lock은 호출자가 잡고 있다고 가정하거나, 필요한 경우 추가 사용
        # 여기서는 값을 읽기만 하므로 안전하다고 가정
        vec = self.current_vector
        
        # 1. 극단적인 감정 상태 우선 확인 (High Intensity)
        if vec.frustration > 0.8: return "angry"     # 극심한 좌절 -> 분노
        if vec.confidence > 0.9: return "joy"        # 극심한 자신감 -> 환희
        if vec.focus > 0.9: return "focused"         # 극심한 집중 -> 집중
        if vec.focus < 0.2 and vec.effort < 0.2: return "bored" # 낮은 집중/노력 -> 지루함
        
        # 2. 복합 감정 상태 확인
        if vec.frustration > 0.4:
            if vec.effort > 0.5: return "pain"       # 좌절 + 노력(힘듦) -> 고통
            if vec.confidence < 0.3: return "sad"    # 좌절 + 낮은 자신감 -> 슬픔
            return "suspicious"                      # 단순 좌절 -> 의심/불만
            
        if vec.curiosity > 0.6:
            if vec.confidence > 0.5: return "excited" # 호기심 + 자신감 -> 흥분/신남
            return "thinking"                         # 호기심 -> 고민/생각
            
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
        """감정 프리셋이 변경되었는지 확인하고 로그를 출력합니다."""
        # 주의: 이 메소드는 _lock 내부에서 호출되어야 함
        new_preset = self.get_closest_preset()
        
        if new_preset != self.last_preset_id:
            # 로그 출력 (YOLO 탐지 포맷과 유사하게)
            # 예: [Emotion] Status Changed: neutral -> happy (conf: 0.85)
            # 주요 원인 벡터 요소 찾기
            vec = self.current_vector
            cause = "neutral"
            max_val = 0.0
            
            # 가장 높은 값을 가진 감정 요소를 '원인'으로 표시
            for k, v in vec.__dict__.items():
                if isinstance(v, (int, float)) and v > max_val:
                    max_val = v
                    cause = k
            
            print(f"[Emotion] Status Changed: {self.last_preset_id.upper()} -> {new_preset.upper()} "
                  f"({cause}: {max_val:.2f})")
            
            self.last_preset_id = new_preset

    def start(self):
        """60Hz 보간 루프를 시작합니다."""
        if self.running: return
        self.running = True
        self.muscles = {} # 파라미터 초기화
        self.last_preset_id = "neutral" # [Phase 2] 초기 프리셋
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
            # [Phase 2] DTO 호환성을 위해 preset_id 포함
            preset = self.get_closest_preset()
            return {
                "vector": self.current_vector.to_dict(),
                "preset_id": preset,
                "muscles": self.muscles
            }

# 싱글톤 인스턴스
emotion_controller = EmotionController()
