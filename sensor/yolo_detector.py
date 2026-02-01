# sensor/yolo_detector.py

import torch
from ultralytics import YOLO

from shared.config import PathConfig

class YoloDetector:
    """
    YOLOv11s 모델을 사용하여 영상 내의 객체를 탐지하는 클래스입니다.
    """
    def __init__(self, model_path: str = None):
        if model_path is None:
            # YOLOv11x (extra-large) 사용 - 최고 정확도
            model_path = str(PathConfig.MODEL_DIR / "yolo11x.pt")
            
        # 연산 장치 설정: GPU 사용 가능 시 cuda, 불가 시 cpu 사용
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        import logging
        logging.info(f"[YoloDetector] 모델 로딩: {model_path} (device: {self.device})")
        
        # 모델 로드 및 장치 할당 (없으면 Ultralytics가 자동 다운로드)
        self.model = YOLO(model_path).to(self.device)
        
        logging.info(f"[YoloDetector] YOLOv11x 모델 로딩 완료 - 클래스 수: {len(self.model.names)}")

    def detect(self, frame):
        """
        입력 영상에서 물체를 찾아 명칭과 중심점 픽셀 좌표 리스트를 반환합니다.
        """
        # 신뢰도(conf) 0.4 이상의 물체만 추출합니다.
        results = self.model(frame, verbose=False, conf=0.4)
        
        detections = []
        if len(results[0].boxes) > 0:
            for box in results[0].boxes:
                # 클래스 ID와 명칭 획득
                cls_id = int(box.cls[0])
                name = self.model.names[cls_id]
                
                # 중심점 좌표(u, v) 계산 (xywh 포맷 사용)
                xywh = box.xywh[0].cpu().numpy()
                u, v = int(xywh[0]), int(xywh[1])
                w, h = int(xywh[2]), int(xywh[3])
                
                detections.append({
                    "name": name,
                    "pixel_center": (u, v),
                    "bbox": (w, h)
                })
        
        return detections