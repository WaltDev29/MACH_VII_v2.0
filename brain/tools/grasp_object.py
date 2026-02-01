# brain/tools/grasp_object.py

from langchain_core.tools import tool
import logging

@tool
def grasp_object(object_name: str = "물체") -> str:
    """
    지정된 물체를 정밀하게 감지하고 잡습니다.
    
    GPD(Grasp Pose Detection), VLM 기반 색상/속성 식별, 
    칼만 필터 추적을 사용하여 정확하게 물체를 잡습니다.
    
    IMPORTANT: object_name은 YOLO가 감지하는 영어 클래스명을 사용해야 합니다.
    예: "kite" (연), "cup" (컵), "bottle" (병), "teddy" (곰인형), "soccerball" (축구공)
    
    색상이 지정된 경우: "yellow kite", "red cup" 형식으로 전달하세요.
    
    사용 예시:
    - "오리" → 시야의 오리를 잡음
    - "노란 연" → 여러 연 중 노란색만 선택하여 잡음
    - "빨간 컵" → 빨간색 컵만 선택하여 잡음
    - "물체" → 가장 가까운 물체 자동 선택
    
    시스템은 다음 과정을 자동으로 수행합니다:
    1. 물체 감지 (YOLO + 칼만 필터)
    2. 색상/속성이 지정된 경우 VLM으로 정확한 객체 식별
    3. 그립 자세 계산 (GPD)
    4. 비주얼 서보잉으로 정밀 접근
    5. 그리퍼로 물체 잡기
    
    Args:
        object_name: 잡을 물체의 이름 (색상, 속성 포함 가능)
    """
    # Strategy Layer로 위임 (아키텍처 준수)
    from strategy.grasp_strategy import execute_grasp
    
    logging.info(f"[GraspTool] '{object_name}' 잡기 요청")
    
    result = execute_grasp(object_name)
    
    return result["message"]
