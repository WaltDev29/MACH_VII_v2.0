# brain/tools/robot/robot_action.py

from langchain_core.tools import tool
from state.system_state import system_state
from shared.state_broadcaster import broadcaster

@tool
def robot_action(intent: str) -> str:
    """
    로봇에게 물리적인 행동을 지시하거나 모드를 변경할 때 사용합니다. 
    예: '인사해라', '잡아라', '멈춰'
    입력값은 로봇의 행동 의도를 나타내는 짧은 명령(intent)입니다.
    """
    # 1. 시스템 상태 업데이트 (Layer 2)
    system_state.current_intent = intent
    
    # 2. 실행 계층으로 의도 전파 (Layer 6을 위한 Signal)
    # 실제로는 SystemPipeline이 이를 감지하여 처리하도록 설계되었습니다.
    broadcaster.publish("action_intent", intent)
    broadcaster.publish("agent_thought", f"[Action] 실행 명령 하달: {intent}")
    
    return f"로봇에게 '{intent}' 동작 수행을 지시했습니다. 하드웨어가 현재 시야 정보를 바탕으로 반응할 것입니다."
