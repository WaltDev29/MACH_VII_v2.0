# sensor/perception_manager.py

import threading
import time
import logging
import base64
import cv2
from .vision_bridge import VisionBridge
from state.system_state import system_state
from shared.state_broadcaster import broadcaster
from shared.config import GlobalConfig

class PerceptionManager:
    """
    비전 센서의 데이터를 주기적으로 수집하여 전역 상태(SystemState)를 업데이트합니다.
    """
    def __init__(self, interval=0.1):
        self.bridge = VisionBridge()
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logging.info("[Sensor] PerceptionManager 루프가 시작되었습니다.")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)

    def _update_loop(self):
        while self.running:
            try:
                # 1. 시각 탐지 및 좌표 산출
                detections = self.bridge.get_refined_detections()
                
                # 2. VLM 분석용 프레임 획득
                raw_frame = self.bridge.get_raw_frame()
                image_b64 = None
                if raw_frame is not None:
                     # JPEG 인코딩 후 Base64 변환
                     ret, buffer = cv2.imencode('.jpg', raw_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                     if ret:
                         image_b64 = base64.b64encode(buffer).decode('utf-8')

                # 3. 전역 상태(Layer 2) 업데이트
                new_perception = {
                    "detected_objects": detections,
                    "detection_count": len(detections),
                    "timestamp": time.time(),
                    "sensor_mode": "Sim" if GlobalConfig.SIM_MODE else "Real"
                }
                
                system_state.perception_data = new_perception
                if image_b64:
                    system_state.last_frame_base64 = image_b64
                
                # 4. 상태 전파
                broadcaster.publish("perception", new_perception)
                
            except Exception as e:
                logging.error(f"[Sensor] Perception 업데이트 오류: {e}")
            
            time.sleep(self.interval)

# 전역 인스턴스
perception_manager = PerceptionManager()
