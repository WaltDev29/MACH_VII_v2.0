from langchain_core.tools import tool
from sensor.vision_bridge import VisionBridge

@tool
def vision_detect(query: str = "detect") -> str:
    """
    실시간 영상에서 물체를 탐지하여 이름과 3D 공간 좌표(cm)를 보고하는 도구입니다.
    로봇 팔로 물체를 잡기 위해 정확한 위치 정보가 필요할 때 사용합니다.
    """
    try:
        # 비전 브릿지를 통해 현재 환경에 맞는 정제된 탐지 데이터를 요청합니다.
        #
        bridge = VisionBridge()
        items = bridge.get_refined_detections()
        
        if not items:
            return "[RESULT] 현재 시야에서 감지된 물체가 없습니다."
            
        # 감지된 물체 리스트를 에이전트가 이해하기 쉬운 문자열로 정제합니다.
        # 모든 좌표 단위는 cm이며, 우측 좌표계 규격을 준수합니다.
        response = "[SUCCESS] 탐지 결과 보고:\n"
        for item in items:
            name = item.get("name", "unknown")
            pos = item.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
            response += f"- {name}: (x={pos['x']}, y={pos['y']}, z={pos['z']}) cm\n"
            
        return response
        
    except Exception as e:
        # 시스템 오류 발생 시 상세 내용을 기록하고 보고합니다.
        return f"[ERROR] 비전 탐지 도구 구동 중 오류 발생: {str(e)}"