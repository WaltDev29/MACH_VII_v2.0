# brain/tools/vision/vision_analyze.py

import base64
import requests
import cv2
from langchain_core.tools import tool
from sensor.vision_bridge import VisionBridge
from shared.config import GlobalConfig

@tool
def vision_analyze(query: str) -> str:
    """
    VLM(Vision-Language Model)을 사용하여 현재 카메라 영상의 상세 내용을 분석합니다.
    물체의 색상, 재질, 텍스트 또는 복잡한 상황을 파악해야 할 때 사용합니다.
    """
    try:
        # 1. 비전 브릿지에서 원본 영상 획득 (Raw RGB Frame)
        bridge = VisionBridge()
        color_frame = bridge.get_raw_frame()
        
        if color_frame is None:
            return "[RESULT] 분석할 영상을 획득하지 못했습니다. 카메라 연결을 확인하세요."

        # 2. 이미지 최적화 (해상도 축소 및 JPEG 인코딩)
        resized_image = cv2.resize(color_frame, (320, 240))
        _, buffer = cv2.imencode('.jpg', resized_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        # 3. 전역 설정의 VLM 서버에 분석 요청
        payload = {
            "model": GlobalConfig.VLM_MODEL,
            "prompt": query,
            "images": [image_base64],
            "stream": False
        }

        response = requests.post(GlobalConfig.VLM_ENDPOINT, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json().get('response', '분석 결과가 없습니다.')
            return f"[SUCCESS] 시각 분석 결과:\n{result}"
        else:
            return f"[FAILURE] VLM 서버 오류 (코드: {response.status_code})"

    except Exception as e:
        return f"[ERROR] VLM 분석 도구 실행 오류: {str(e)}"