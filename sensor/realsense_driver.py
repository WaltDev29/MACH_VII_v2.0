# sensor/realsense_driver.py

import time
import threading
import numpy as np
import logging
import cv2
from typing import Optional, Tuple

# 1. RealSense 라이브러리 가용성 체크
RS_AVAILABLE = False
try:
    import pyrealsense2 as rs
    RS_AVAILABLE = True
except ImportError:
    RS_AVAILABLE = False

class RealSenseDriver:
    """
    RealSense 하드웨어와 직접 통신하여 프레임을 제공하는 저수준 드라이버입니다.
    AI 분석이나 상태 업데이트 로직을 포함하지 않고 오직 데이터 획득에만 집중합니다.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RealSenseDriver, cls).__new__(cls)
        return cls._instance

    def __init__(self, fps=30):
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        self.fps = fps
        self.running = False
        self.thread = None
        self.pipeline = None
        self.config = None
        
        # 최신 프레임 저장소
        self.latest_color = None
        self.latest_depth = None
        self.frame_lock = threading.Lock()
        
        logging.info(f"[Sensor] RealSense 드라이버 초기화됨 (RS_AVAILABLE={RS_AVAILABLE})")
        self.initialized = True

    def start(self):
        if not RS_AVAILABLE:
            logging.error("[Sensor] RealSense 라이브러리를 찾을 수 없어 드라이버를 시작할 수 없습니다.")
            return

        if self.running:
            return

        try:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, self.fps)
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, self.fps)
            
            self.pipeline.start(self.config)
            self.running = True
            
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logging.info("[Sensor] RealSense 캡처 루프가 시작되었습니다.")
        except Exception as e:
            logging.error(f"[Sensor] RealSense 시작 실패: {e}")
            self.pipeline = None

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.pipeline:
            try:
                self.pipeline.stop()
            except:
                pass
            self.pipeline = None
        logging.info("[Sensor] RealSense 드라이버가 중지되었습니다.")

    def _capture_loop(self):
        while self.running:
            try:
                frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                
                if not depth_frame or not color_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())

                with self.frame_lock:
                    self.latest_color = color_image
                    self.latest_depth = depth_image
                    
            except Exception as e:
                logging.warning(f"[Sensor] 캡처 중 오류 발생: {e}")
                time.sleep(0.1)

            time.sleep(1.0 / self.fps)

    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """현재 가장 최신의 RGB 및 Depth 프레임을 반환합니다."""
        with self.frame_lock:
            return self.latest_color, self.latest_depth

    def generate_rgb_stream(self):
        """Web UI 스트리밍을 위한 MJPEG 제너레이터"""
        while True:
            color, _ = self.get_frames()
            if color is not None:
                ret, buffer = cv2.imencode('.jpg', color, [cv2.IMWRITE_JPEG_QUALITY, 60])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1.0 / self.fps)

# 싱글톤 인스턴스
realsense_driver = RealSenseDriver()
