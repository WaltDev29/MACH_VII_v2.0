import time
import threading
from shared.state_broadcaster import broadcaster
from expression.emotion_controller import emotion_controller

class LLMUpdater:
    """
    축적된 컨텍스트를 기반으로 LLM(Gemma3)에게 감정 목표 조정을 요청하거나,
    간단한 규칙(Rule-based)을 통해 주기적으로 감정 상태를 업데이트하는 저빈도(Low-rate) 루프입니다.
    
    주요 기능:
    - 2초마다 실행되며, 브로드캐스터로부터 현재 상황을 파악합니다.
    - 너무 오래 할 일이 없으면(Idle) 지루함을 느껴 호기심(Curiosity)을 높입니다.
    - 행동 결과(성공/실패)에 따라 자신감(Confidence)을 조절합니다.
    """
    def __init__(self):
        self.running = False
        
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False
        print("[Emotion-LLM] 업데이터 종료됨.")
        
    def _loop(self):
        print("[Emotion-LLM] 업데이터 시작됨 (Low-rate).")
        idle_start_time = 0
        
        while self.running:
            # 저빈도: 2초마다 실행
            time.sleep(2.0)
            
            # 컨텍스트 획득
            context = broadcaster.get_snapshot()
            agent_state = context.get("agent_state", "IDLE")
            
            # 휴리스틱 로직 (LLM 추론 시뮬레이션)
            updates = {}
            
            # 1. 지루함 메커니즘 (너무 오래 IDLE 상태인 경우)
            if agent_state == "IDLE":
                if idle_start_time == 0:
                    idle_start_time = time.time()
                elif time.time() - idle_start_time > 10.0:
                    # 지루함 -> 호기심 증가
                    # print("[Emotion-LLM] 에이전트가 지루해합니다. 호기심을 증가시킵니다.")
                    updates["curiosity"] = 0.8
            else:
                idle_start_time = 0
                
            # 2. 자신감 확인 (성공/실패 여부)
            episode_result = context.get("episode_result", "none")
            if episode_result == "success":
                # 성공 시 자신감 대폭 상승
                updates["confidence"] = 0.9
            elif episode_result == "failure":
                # 실패 시 자신감 하락 (위축)
                updates["confidence"] = 0.2
                
            # 변경사항이 있다면 감정 컨트롤러에 반영 요청
            # update_target 함수는 잠시동안 자동 감정 변화를 멈추고 이 값을 우선 적용합니다.
            if updates:
                emotion_controller.update_target(updates)

# 싱글톤
llm_updater = LLMUpdater()
