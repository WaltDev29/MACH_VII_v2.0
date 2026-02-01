# sensor/vision_bridge.py

import logging
from shared.config import GlobalConfig, CameraConfig
from sensor.pybullet_vision import PybulletVision
from sensor.realsense_vision import RealSenseVision
from sensor.yolo_detector import YoloDetector
from state.system_state import system_state
import threading
import time
import numpy as np

class VisionBridge:
    """
    하드웨어 드라이버와 AI 모델을 연결하고, 동기화된 데이터를 바탕으로
    로봇 베이스 기준의 정밀 좌표를 산출하는 통합 관리 클래스입니다.
    """
    def __init__(self):
        # 1. 시스템 설정에서 시뮬레이션 모드 여부를 확인합니다.
        self.sim_mode = GlobalConfig.SIM_MODE

        # 2. 모드에 따라 적절한 드라이버와 카메라 오프셋을 설정합니다.
        if self.sim_mode:
            self.driver = PybulletVision()
            self.offset = CameraConfig.SIM_OFFSET
        else:
            self.driver = RealSenseVision()
            self.offset = CameraConfig.REAL_OFFSET

        # 3. 객체 탐지를 위한 YOLOv11 엔진을 초기화합니다.
        self.yolo = YoloDetector()

        # 4. 백그라운드 업데이트 스레드 관리
        self.running = False
        self.update_thread = None

    def switch_source(self, source: str):
        """실시간으로 카메라 소스를 전환합니다 (pybullet / realsense)"""
        from shared.ui_dto import CameraSource
        if source == CameraSource.VIRTUAL:
            self.driver = PybulletVision()
            self.offset = CameraConfig.SIM_OFFSET
            self.sim_mode = True
        else:
            self.driver = RealSenseVision()
            self.offset = CameraConfig.REAL_OFFSET
            self.sim_mode = False
        print(f"[VisionBridge] 소스 전환 완료: {source}")

    def get_raw_frame(self):
        """
        VLM 분석을 위해 처리되지 않은 원본 영상 데이터를 반환합니다.
        동기화 패키지에서 컬러 영상만 추출하여 제공합니다.
        """
        packet = self.driver.get_synced_packet()
        if not packet:
            return None
        return packet.get("color")

    def get_refined_detections(self):
        """
        동기화된 영상과 포즈 데이터를 사용하여 물체를 탐지하고,
        카메라 오프셋을 적용한 로봇 베이스 기준의 cm 좌표를 반환합니다.
        """
        # 1. 영상, 깊이, 로봇 포즈가 한 세트로 묶인 동기화 패키지를 획득합니다.
        packet = self.driver.get_synced_packet()
        if not packet:
            logging.warning("[VisionBridge] 동기화 패키지를 획득하지 못했습니다.")
            return []

        color_frame = packet.get("color")
        depth_frame = packet.get("depth")
        captured_pose = packet.get("captured_pose", {})
        
        if color_frame is None or depth_frame is None:
            logging.error(f"[VisionBridge] 불완전한 데이터 (color={color_frame is not None}, depth={depth_frame is not None})")
            return []

        # 2. YOLO 엔진을 사용하여 영상 내 객체의 2D 픽셀 좌표를 탐지합니다.
        raw_detections = self.yolo.detect(color_frame)
        logging.info(f"[VisionBridge] YOLO 탐지 결과: {len(raw_detections)}개 물체")
        
        refined_list = []
        for i, det in enumerate(raw_detections):
            u, v = det["pixel_center"]
            
            # 3. 해당 픽셀의 깊이 정보(실제 미터)를 가져옵니다.
            # 물체의 표면이 아닌 중심 깊이를 추정하기 위해 ROI 분석을 수행합니다.
            
            # ROI를 BBox의 40% 크기(중앙 집중)로 설정하여 배경 혼입을 방지합니다.
            margin_w = int(det["bbox"][0] * 0.3) # 좌우 30%씩 버림 -> 중앙 40% 사용
            margin_h = int(det["bbox"][1] * 0.3)
            
            u_min = max(0, u - det["bbox"][0] // 2 + margin_w)
            u_max = min(depth_frame.shape[1], u + det["bbox"][0] // 2 - margin_w)
            v_min = max(0, v - det["bbox"][1] // 2 + margin_h)
            v_max = min(depth_frame.shape[0], v + det["bbox"][1] // 2 - margin_h)
            
            depth_roi = depth_frame[v_min:v_max, u_min:u_max]
            
            # 유효한 Depth 값만 필터링 (0보단 크고 3m 이내)
            valid_depths = depth_roi[(depth_roi > 0) & (depth_roi < 3.0)]
            
            if len(valid_depths) > 0:
                # [적응형 중심 추정 알고리즘]
                # 1. Median: 물체 표면의 대표값 (이상치 제거)
                # 2. Std(표준편차): 물체의 입체감(곡률) 척도
                # 구형 물체는 ROI 내 깊이 변화(편차)가 크므로 더 많이 보정하고,
                # 평평한상자는 편차가 작으므로 적게 보정합니다.
                # Center Depth ≈ Median + Std
                median_d = float(np.median(valid_depths))
                std_d = float(np.std(valid_depths))
                
                depth_m = median_d + std_d
                
                log_msg = f"Depth(Median={median_d:.4f} + Std={std_d:.4f})={depth_m:.4f}m"
            else:
                depth_m = depth_frame[v, u] if v < depth_frame.shape[0] and u < depth_frame.shape[1] else 0
                log_msg = f"Depth(Point)={depth_m:.4f}m"

            logging.info(f"[VisionBridge] 물체 #{i} '{det['name']}': "
                        f"픽셀=({u}, {v}), ROI샘플수={len(valid_depths)}, {log_msg}")
            
            if depth_m <= 0:
                logging.warning(f"[VisionBridge] 물체 #{i} '{det['name']}': 유효하지 않은 깊이 값 ({depth_m})")
                continue
            
            world_coords = self.driver.pixel_to_cm(u, v, depth_m)
            
            if world_coords:
                # PyBullet projection은 월드 좌표 반환 → 오프셋 불필요
                # RealSense는 카메라 좌표 반환 → 오프셋 필요
                # 드라이버 타입에 따라 분기
                driver_type = type(self.driver).__name__
                
                if driver_type == "PybulletVision":
                    # PyBullet: 이미 월드 좌표이므로 그대로 사용
                    robot_x, robot_y, robot_z = world_coords[0], world_coords[1], world_coords[2]
                    logging.info(f"[VisionBridge] 물체 #{i} '{det['name']}': "
                               f"월드좌표=({robot_x:.2f}, {robot_y:.2f}, {robot_z:.2f})cm (오프셋 적용 안 함)")
                else:
                    # RealSense: 카메라 좌표이므로 오프셋 적용
                    robot_x = world_coords[0] + self.offset["x"]
                    robot_y = world_coords[1] + self.offset["y"]
                    robot_z = world_coords[2] + self.offset["z"]
                    logging.info(f"[VisionBridge] 물체 #{i} '{det['name']}': "
                               f"카메라좌표=({world_coords[0]:.2f}, {world_coords[1]:.2f}, {world_coords[2]:.2f})cm "
                               f"+ 오프셋({self.offset['x']}, {self.offset['y']}, {self.offset['z']})cm "
                               f"→ 로봇베이스=({robot_x:.2f}, {robot_y:.2f}, {robot_z:.2f})cm")
                
                # 5. 탐지 결과와 함께 당시 로봇의 위치(Sync Pose)를 패키징하여 반환합니다.
                refined_list.append({
                    "name": det["name"],
                    "position": {
                        "x": round(robot_x, 2),
                        "y": round(robot_y, 2),
                        "z": round(robot_z, 2)
                    },
                    "bbox": det.get("bbox", (0, 0)),
                    "sync_pose": captured_pose
                })
            else:
                logging.warning(f"[VisionBridge] 물체 #{i} '{det['name']}': 좌표 변환 실패")
                
        logging.info(f"[VisionBridge] 최종 탐지 결과: {len(refined_list)}개 물체 좌표 반환")
        return refined_list

    def start_continuous_update(self, interval: float = 0.03):
        """
        비전 데이터를 백그라운드에서 주기적으로 갱신하는 스레드를 시작합니다.
        
        Args:
            interval: 갱신 주기 (초), 기본값 0.03초 (약 30Hz)
        """
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, args=(interval,), daemon=True)
        self.update_thread.start()
        logging.info("[VisionBridge] 연속 비전 업데이트 스레드 시작 (30Hz)")

    def stop_continuous_update(self):
        """비전 업데이트 스레드를 중지합니다."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
        logging.info("[VisionBridge] 연속 비전 업데이트 스레드 중지")

    def _update_loop(self, interval: float):
        """백그라운드에서 실행되는 메인 루프"""
        while self.running:
            try:
                # 1. 최신 탐지 결과 획득
                detections = self.get_refined_detections()
                
                # 2. SystemState 업데이트 (Thread-safe)
                # perception_data 전체를 교체
                system_state.perception_data = {
                    "timestamp": time.time(),
                    "detected_objects": detections,
                    "count": len(detections)
                }
                
                time.sleep(interval)
            except Exception as e:
                logging.error(f"[VisionBridge] 업데이트 루프 오류: {e}")
                time.sleep(1.0) # 오류 발생 시 잠시 대기

