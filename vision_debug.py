# vision_debug.py
"""
비전 시스템 디버그 도구 (Client Mode)
- MAIN.py의 WebSocket 서버에 접속하여 영상을 수신합니다.
- YOLO 탐지 결과 및 칼만 필터 데이터를 시각화합니다.
"""

import cv2
import numpy as np
import time
import logging
import websocket
import json
import base64
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 설정값
WS_URL = "ws://localhost:8000/ws"

class VisionDebuggerClient:
    def __init__(self):
        self.running = True
        self.latest_frame = None
        self.latest_perception = {}
        self.fps = 0
        self.last_time = time.time()
        self.ws = None

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            
            # 1. 프레임 디코딩
            b64_frame = data.get("last_frame")
            if b64_frame:
                img_data = base64.b64decode(b64_frame)
                np_arr = np.frombuffer(img_data, np.uint8)
                self.latest_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            
            # 2. 인식 데이터 갱신
            self.latest_perception = data.get("perception", {})
            
        except Exception as e:
            logging.error(f"메시지 처리 오류: {e}")

    def on_error(self, ws, error):
        logging.error(f"WebSocket 오류: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        logging.info("WebSocket 연결 종료")
        self.running = False

    def on_open(self, ws):
        logging.info(f"서버에 연결되었습니다: {WS_URL}")

    def ws_thread_func(self):
        self.ws = websocket.WebSocketApp(WS_URL,
                                         on_open=self.on_open,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.run_forever()

    def draw_overlays(self, frame, perception):
        """탐지 정보를 프레임 위에 그립니다."""
        display_frame = frame.copy()
        h, w = frame.shape[:2]
        
        detections = perception.get("detected_objects", [])
        
        info_y = 30
        for i, det in enumerate(detections):
            # 좌표는 VisionBridge에서 이미 보정되어 옴 (Refined)
            name = det.get("name", "Unknown")
            pos = det.get("position", {"x": 0, "y": 0, "z": 0})
            bbox = det.get("bbox", [0, 0, 0, 0])
            
            # BBox 그리기 (만약 BBox 정보가 있다면)
            # 주의: VisionBridge가 BBox를 보내주는지 확인 (Step 27 확인 결과 보냄)
            # Step 27: "bbox": det.get("bbox", (0, 0)) <- (w, h)인지 (x, y, w, h)인지 확인 필요
            # YoloDetector(Step 27) detect return: "pixel_center": (u, v), "bbox": (w, h) 형식임
            # 하지만 정확한 픽셀 위치 재구성을 위해선 center가 필요.
            # 하지만 여기서는 'refined' result만 오므로, 2D 박스를 정확히 그리기 어려울 수 있음.
            # packet에 'pixel_center'나 'bbox' center가 없다면 그리기 어려움.
            
            # VisionBridge는 'detection' dict에 "pixel_center"를 포함하지 않고 있었음 (Step 27).
            # 단, 좌표 텍스트 표시는 가능함.
            
            text = f"{name}: ({pos['x']:.1f}, {pos['y']:.1f}, {pos['z']:.1f}) cm"
            cv2.putText(display_frame, text, (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            info_y += 25
            
        # FPS 표시
        cv2.putText(display_frame, f"Stream FPS: {self.fps:.1f}", (w - 180, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        status = f"Objects: {len(detections)} | Mode: {perception.get('sensor_mode', 'Unknown')}"
        cv2.putText(display_frame, status, (10, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display_frame

    def run(self):
        # 1. WebSocket 스레드 시작
        t = threading.Thread(target=self.ws_thread_func, daemon=True)
        t.start()
        
        print("=" * 60)
        print("비전 디버거 클라이언트 모드")
        print(f"대상 서버: {WS_URL}")
        print("=" * 60)

        frame_count = 0
        start_time = time.time()

        try:
            while self.running:
                if self.latest_frame is not None:
                    # 2. 시각화
                    display_frame = self.draw_overlays(self.latest_frame, self.latest_perception)
                    
                    # 3. FPS 계산
                    frame_count += 1
                    elapsed = time.time() - start_time
                    if elapsed > 1.0:
                        self.fps = frame_count / elapsed
                        frame_count = 0
                        start_time = time.time()
                    
                    cv2.imshow("Review Vision Debug", display_frame)
                    
                    # 4. 프레임 소모 (중복 렌더링 방지용 - 선택적)
                    # self.latest_frame = None 
                else:
                    # 연결 대기 중 화면
                    blank = np.zeros((480, 640, 3), np.uint8)
                    cv2.putText(blank, "Waiting for stream...", (200, 240), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
                    cv2.imshow("Review Vision Debug", blank)
                
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            if self.ws:
                self.ws.close()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    client = VisionDebuggerClient()
    client.run()
