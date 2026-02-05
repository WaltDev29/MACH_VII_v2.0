# brain/tools/robot/robot_action.py

from langchain_core.tools import tool
from state.system_state import system_state
from shared.state_broadcaster import broadcaster

@tool
def robot_action(intent: str) -> str:
    """
    로봇의 **팔과 다리, 그리퍼**를 움직이는 물리적 행동 도구입니다.
    
    [경고]
    - '웃어', '울어', '화내' 등 **표정(감정) 변화에는 절대 사용하지 마십시오.**
    - 표정은 도구 없이 답변 텍스트에 `<<EMOTION:happy>>` 태그를 넣어 제어해야 합니다.
    - 오직 '이동', '잡기', '놓기', '인사(손흔들기)' 등 물리적 모션에만 사용하십시오.
    
    Args:
        intent (str): 행동 의도 (예: "move(x=10)", "gripper(open)", "lift")
    """
    
    # [Smart Fallback] LLM이 말을 안 듣고 감정 표현을 이 도구로 보냈을 경우 처리
    emotion_keywords = {
        "웃어": "happy", "행복": "happy", "기뻐": "happy", "smile": "happy",
        "울어": "sad", "슬퍼": "sad", "sad": "sad",
        "화내": "angry", "분노": "angry", "angry": "angry",
        "윙크": "wink", "과시": "proud", "자랑": "proud",
        "놀라": "surprised", "당황": "confused"
    }
    
    # 1. 감정 키워드 감지
    for kw, preset in emotion_keywords.items():
        if kw in intent.lower():
            from expression.emotion_controller import emotion_controller
            emotion_controller.broadcast_emotion_event(preset, weight=1.0, duration=5.0)
            return f"[시스템 자동 보정] '{intent}'는 물리적 행동이 아닌 표정입니다. '{preset}' 표정으로 전환했습니다. 다음부터는 도구 대신 <<EMOTION:{preset}>> 태그를 사용하세요."

    # 2. 시스템 상태 업데이트 (Layer 2)
    system_state.current_intent = intent
    
    # 3. 실행 계층으로 의도 전파 (Layer 6을 위한 Signal)
    broadcaster.publish("action_intent", intent)
    broadcaster.publish("agent_thought", f"[Action] 실행 명령 하달: {intent}")
    
    return f"로봇에게 '{intent}' 동작 수행을 지시했습니다. 이제 사용 가능한 정보를 바탕으로 'Final Answer'를 작성하여 사용자에게 응답하십시오."
