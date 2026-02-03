# shared/pipeline.py

import threading
import time
from typing import Dict, Any, List, Optional
from shared.state_broadcaster import broadcaster
from state.system_state import system_state
from strategy.strategy_manager import strategy_manager
from shared.intents import ActionIntent
from memory.falkordb_manager import memory_manager
from shared.ui_dto import SystemSnapshot
import uuid

class SystemPipeline:
    """
    싱글톤 패턴으로 7-레이어 아키텍처의 단방향 데이터 흐름을 오케스트레이션하는 클래스입니다.
    Sensor -> State -> Brain -> Strategy -> Expression -> Embodiment -> Memory
    순서로 데이터가 흐르도록 제어합니다.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SystemPipeline, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.running = False
        self.components = {} # 각 레이어의 핸들러 등록 공간
        self.emotion_ctrl = None # 자주 쓰이는 감정 컨트롤러 캐싱용

    def register_component(self, name: str, component: Any):
        """레이어별 컴포넌트를 등록합니다."""
        self.components[name] = component
        if name == "emotion_controller":
            self.emotion_ctrl = component
        print(f"[Pipeline] 컴포넌트 등록됨: {name}")
        # 각 모듈이 시작될 때 파이프라인을 등록하고 정상 등록 상황을 로그로 확인할 수 있도록 함

    def process_brain_intent(self, intent: Any):
        """
        Brain에서 결정된 의도(Intent)를 파이프라인의 후속 단계로 흘려보냅니다.
        Brain (Layer 3) -> Strategy (Layer 4) -> Expression (Layer 5) -> Embodiment (Layer 6) -> Memory (Layer 7)
        """
        # 0. 의도 표준화 (Standardization)
        if isinstance(intent, str):
            intent_enum = ActionIntent.from_str(intent)
        elif isinstance(intent, ActionIntent):
            intent_enum = intent
        else:
            intent_enum = ActionIntent.UNKNOWN

        print(f"\n[Pipeline] === 파이프라인 실행 시작 (Intent: {intent_enum.name}) ===")
        
        # 시작 감정 상태 수집 (Layer 5 이전)
        start_emotion = self.emotion_ctrl.get_current_emotion()["vector"] if self.emotion_ctrl else [0]*6

        # 1. Strategy Filtering (Layer 4)
        # strategy_manager에게 "이 행동을 해도 안전한가?" 혹은 "지금 상황에 맞는가?" 등을 확인
        if not strategy_manager.filter_action(intent_enum.value):
            print(f"[Pipeline] [Layer 4: Strategy] 행동이 차단되었습니다: {intent_enum.name}")
            broadcaster.publish("agent_thought", f"[Strategy] 현재 전략 모드에서 차단된 행동입니다: {intent_enum.name}")
            return

        # 2. Expression / Emotion Mapping (Layer 5)
        # 표준화된 의도에 따른 감정 상태 변화 유도
        # 표정부 완전 구현 시 수정 예정
        emotion_patch = {}
        if intent_enum == ActionIntent.GREET:
            emotion_patch = {"confidence": 0.8, "frustration": 0.0}
        elif intent_enum == ActionIntent.PICK_UP:
            emotion_patch = {"focus": 1.0, "effort": 0.7}
        elif intent_enum == ActionIntent.STOP:
            emotion_patch = {"frustration": 0.5, "focus": 0.8}
        
        if emotion_patch and self.emotion_ctrl:
            self.emotion_ctrl.update_target(emotion_patch)
        
        # 종료(목표) 감정 상태 수집
        end_emotion = self.emotion_ctrl.get_current_emotion()["vector"] if self.emotion_ctrl else [0]*6

        # 3. Embodiment Execution (Layer 6)
        # broadcaster.publish를 통해 제어 루프에 신호 전달
        system_state.current_intent = intent_enum.value
        broadcaster.publish("action_intent", intent_enum.value)
        
        # 4. Memory Archiving (Layer 7)
        # 최종 판단과 감정 변화를 메모리에 기록
        try:
            episode_id = f"ep_{int(time.time())}_{uuid.uuid4().hex[:4]}"
            episode_data = {
                "id": episode_id,
                "timestamp": time.time(),
                "result": "executed", # 실행 명령 하달 성공
                "action": {"type": intent_enum.name, "target": "system"},
                "start_emotion": start_emotion,
                "end_emotion": end_emotion
            }
            memory_manager.save_episode(episode_data)
            print(f"[Pipeline] [Layer 7: Memory] 에피소드 저장 완료: {episode_id}")
        except Exception as e:
            print(f"[Pipeline] [Layer 7: Memory] 저장 중 오류: {e}")
        
        print("[Pipeline] === 파이프라인 실행 완료 ===\n")

    def get_system_snapshot(self) -> Dict[str, Any]:
        """
        단방향 흐름에 따라 수집된 전체 시스템 상태의 정합성 있는 스냅샷을 반환하는 종합 메소드.
        UI 스트리밍 등에 사용됩니다.
        """
        # [Phase 2] SystemSnapshot DTO를 사용하여 데이터 구조의 일관성을 강제합니다.
        
        # 감정 데이터 준비
        emotion_data = self.emotion_ctrl.get_current_emotion() if self.emotion_ctrl else {
             "vector": {}, "muscles": {}, "preset_id": "neutral"
        }

        # DTO 생성
        snapshot = SystemSnapshot(
            timestamp=time.time(),
            brain=broadcaster.get_snapshot(),
            emotion=emotion_data,
            perception=system_state.perception_data,
            robot={
                "is_moving": system_state.robot.is_moving,
                "battery": system_state.robot.battery_level,
                "mode": system_state.robot.current_mode
            },
            strategy=strategy_manager.get_context().copy(), # 복사본 사용
            last_frame=system_state.last_frame_base64
        )
        
        return snapshot.dict()

# 싱글톤 인스턴스
pipeline = SystemPipeline()
