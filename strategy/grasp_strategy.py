# strategy/grasp_strategy.py

from sensor.vision_bridge import VisionBridge
from strategy.grasp_planner import grasp_planner
from state.system_state import system_state
from shared.state_broadcaster import broadcaster
import logging

def execute_grasp(object_name: str) -> dict:
    """
    물체 잡기 전략을 실행합니다.
    
    GPD, VLM 식별, 칼만 필터를 활용하여 정밀한 객체 잡기를 수행합니다.
    Brain Layer에서 호출되며, Strategy Layer가 실제 로직을 담당합니다.
    
    Args:
        object_name: 잡을 물체의 이름 (색상, 속성 포함 가능)
                    예: "오리", "노란 연", "빨간 컵", "물체"
    
    Returns:
        {"success": bool, "message": str, "target": str}
    """
    try:
        # 1. 비전 시스템으로 물체 탐지 (칼만 필터 적용됨)
        logging.info(f"[GraspStrategy] '{object_name}' 탐지 시작...")
        vision = VisionBridge()
        detections = vision.get_refined_detections()
        
        if not detections:
            return {
                "success": False,
                "message": "[실패] 시야에서 물체를 발견하지 못했습니다."
            }
        
        # 2. VLM 기반 정확한 객체 식별
        target = _identify_target_object(object_name, detections)
        
        if not target:
            detected_names = [d['name'] for d in detections]
            return {
                "success": False,
                "message": f"[실패] '{object_name}'을(를) 찾을 수 없습니다. 감지된 물체: {detected_names}"
            }
        
        obj_name = target['name']
        obj_pos = target['position']
        obj_bbox = target.get('bbox', (0, 0))
        
        logging.info(f"[GraspStrategy] 목표 물체: {obj_name} at ({obj_pos['x']:.1f}, {obj_pos['y']:.1f}, {obj_pos['z']:.1f})cm")
        
        # 3. GPD로 그립 자세 계산
        grasp_pose = grasp_planner.compute_grasp_pose(obj_name, obj_pos, bbox=obj_bbox)
        
        # 4. Intent를 system_state에 저장 및 broadcast
        # RobotController가 이를 구독하여 visual_servoing 실행
        import time
        intent_data = {
            "action": "GRASP",
            "target_name": obj_name,
            "target_position": obj_pos,
            "grasp_pose": grasp_pose,
            "timestamp": time.time()  # 중복 방지용
        }
        
        system_state.current_intent = f"grasp_{obj_name}"
        broadcaster.publish("grasp_intent", intent_data)
        
        logging.info(f"[GraspStrategy] '{obj_name}' 잡기 명령 발행")
        
        return {
            "success": True,
            "message": f"{object_name}을(를) 잡기 위한 명령을 전송했습니다.",
            "target": obj_name
        }
        
    except Exception as e:
        logging.error(f"[GraspStrategy] 오류: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "success": False,
            "message": f"[오류] {str(e)}"
        }


def _identify_target_object(object_name: str, detections: list) -> dict:
    """
    VLM을 활용하여 정확한 타겟 객체를 식별합니다.
    
    - 색상/속성 고려 (예: "노란 연", "빨간 컵")
    - 의미적 매칭 (YOLO 클래스명 불일치 시)
    
    Args:
        object_name: 사용자가 요청한 물체 이름
        detections: VisionBridge에서 탐지된 물체 리스트
        
    Returns:
        타겟 물체 딕셔너리 또는 None
    """
    # 색상 키워드 감지
    color_keywords = [
        "red", "yellow", "blue", "green", "white", "black", "purple", "pink",
        "orange", "빨간", "빨강", "노란", "노랑", "파란", "파랑", "초록", 
        "흰", "검은", "검정", "보라", "분홍"
    ]
    has_color = any(kw in object_name.lower() for kw in color_keywords)
    
    target = None
    
    # 색상이 지정된 경우 VLM으로 정확한 위치 식별
    if has_color and len(detections) > 1:
        logging.info(f"[GraspStrategy] 색상/속성 감지 - VLM으로 '{object_name}' 식별 중...")
        
        from brain.tools.vision_analyze import vision_analyze
        
        query = f"화면에 보이는 물체들 중에서 '{object_name}'의 위치를 알려주세요. " \
                f"왼쪽, 중앙, 오른쪽 중 어디에 있나요?"
        
        vlm_result = vision_analyze.invoke({"query": query})
        logging.info(f"[GraspStrategy] VLM 분석 결과: {vlm_result}")
        
        vlm_lower = vlm_result.lower()
        
        # 위치 기반 필터링
        if "왼쪽" in vlm_lower or "left" in vlm_lower:
            target = min(detections, key=lambda d: d['position']['x'])
        elif "오른쪽" in vlm_lower or "right" in vlm_lower:
            target = max(detections, key=lambda d: d['position']['x'])
        elif "중앙" in vlm_lower or "center" in vlm_lower or "가운데" in vlm_lower:
            target = min(detections, key=lambda d: abs(d['position']['x']))
        else:
            # VLM이 명확한 위치를 제공하지 못한 경우, 가장 가까운 물체 선택
            target = min(detections, key=lambda d: 
                        (d['position']['x']**2 + 
                         d['position']['y']**2 + 
                         d['position']['z']**2)**0.5)
            logging.warning(f"[GraspStrategy] VLM 위치 불명확 - 가장 가까운 물체 선택")
    
    # 일반 객체 선택
    if not target:
        if object_name == "물체":
            # 가장 가까운 물체
            target = min(detections, key=lambda d: 
                        (d['position']['x']**2 + 
                         d['position']['y']**2 + 
                         d['position']['z']**2)**0.5)
        else:
            # 이름 매칭 (부분 일치)
            for det in detections:
                det_name = det['name'].lower()
                search_name = object_name.lower()
                
                # "yellow kite" → "kite" 추출하여 매칭
                if search_name in det_name or det_name in search_name:
                    target = det
                    break
    
    # VLM 의미적 매칭 (이름 불일치 시)
    if not target and detections:
        logging.info(f"[GraspStrategy] '{object_name}' 이름 일치 실패. VLM에게 의미적 매칭 요청...")
        
        from brain.tools.vision_analyze import vision_analyze
        
        detected_names = [d['name'] for d in detections]
        query = f"나 지금 '{object_name}'을(를) 잡고 싶은데, 내 눈에는 {detected_names}만 보여. " \
                f"이 목록 중에서 '{object_name}'일 가능성이 가장 높은 것은 뭐야? " \
                f"목록에 있는 정확한 이름을 반환해줘. 매칭되는게 없으면 'NONE'이라고 답해줘."
        
        vlm_response = vision_analyze.invoke({"query": query})
        logging.info(f"[GraspStrategy] VLM Semantic Matching result: {vlm_response}")
        
        # VLM 응답과 일치하는 YOLO 물체 찾기
        for det in detections:
            if det['name'].lower() in vlm_response.lower():
                target = det
                logging.info(f"[GraspStrategy] VLM이 '{det['name']}'을(를) '{object_name}'(으)로 식별했습니다.")
                break
    
    return target
