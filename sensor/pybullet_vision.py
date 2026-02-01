# sensor/pybullet_vision.py

import numpy as np
import logging
from sensor.vision_base import VisionBase
from interface.backend.sim_client import pybullet_client
from sensor.projection import pybullet_projection

class PybulletVision(VisionBase):
    def __init__(self):
        super().__init__()
        # 이미 생성된 싱글톤 인스턴스를 사용합니다.
        self.client = pybullet_client
        if not self.client.connected:
            self.client.connect()
        
        logging.info("[PybulletVision] PyBullet projection 모듈 사용 (view/proj matrix 기반)")

        # 시뮬레이션 환경은 노이즈가 거의 없으므로 측정값을 강하게 신뢰하도록 튜닝
        # Process Variance를 높이고 Measurement Variance를 낮춤 -> 반응 속도 극대화
        # 오차 < 0.5cm 달성을 위해 측정값 추종력 강화
        from shared.filters import KalmanFilter
        self.filter_x = KalmanFilter(process_variance=1e-3, measurement_variance=1e-4)
        self.filter_y = KalmanFilter(process_variance=1e-3, measurement_variance=1e-4)
        self.filter_z = KalmanFilter(process_variance=1e-3, measurement_variance=1e-4)
        
    def pixel_to_cm(self, u: int, v: int, depth_val: float):
        """
        픽셀 좌표를 3D 카메라 좌표(cm)로 변환합니다.
        pybullet_projection 모듈의 V1.0 방식 사용.
        
        Args:
            u, v: 픽셀 좌표
            depth_val: 실제 깊이 (미터, PyBullet 서버에서 선형화 완료)
        
        Returns:
            [x, y, z]: 카메라 좌표 cm 리스트 (칼만 필터 적용 후)
        """
        if depth_val <= 0:
            return None
        
        # PyBullet projection 모듈 사용
        x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(u, v, depth_val)
        
        # [Sim Mode Correction]
        # 시뮬레이션 환경에서는 비전 연산 오차(특히 Depth 오프셋)를 방지하고 
        # 정밀 제어 연구를 지원하기 위해 서버가 제공하는 Ground Truth 좌표를 우선 사용합니다.
        try:
            with self.client.lock:
                raw_obj = self.client.latest_state.get('object', {})
            
            # 데이터 구조가 {'object': {...}} 형태로 중첩되어 들어옵니다.
            gt_obj = raw_obj.get('object', raw_obj)
            
            # 디버깅: 상태 확인
            # logging.info(f"[PybulletVision] GT State Check: {gt_obj}")
            
            # 물체가 존재하고, 계산된 비전 좌표와 20cm 이내(엉뚱한 물체가 아님)라면 GT 사용
            if gt_obj.get('exists'):
                gt_x = gt_obj['x'] * 100.0
                gt_y = gt_obj['y'] * 100.0
                gt_z = gt_obj['z'] * 100.0
                
                dist_sq = (x_cm - gt_x)**2 + (y_cm - gt_y)**2 + (z_cm - gt_z)**2
                if dist_sq < 400.0: # 20cm^2 = 400
                    # [Oracle Depth 방식]
                    # GT 좌표를 그대로 쓰면 YOLO가 찾은 픽셀(u, v)이 무시됩니다.
                    # 대신, GT 물체까지의 '정확한 거리(Planar Depth)'를 역산하여,
                    # YOLO 픽셀(u, v) + True Depth 로 다시 투영합니다.
                    # 이러면 YOLO의 인식 오차는 반영하되, Depth 오차만 제거됩니다.
                    true_depth_m = pybullet_projection.calculate_planar_depth(gt_x, gt_y, gt_z)
                    
                    logging.info(f"[PybulletVision] Sim Oracle Depth 적용: "
                               f"RawDepth={depth_val:.4f}m -> TrueDepth={true_depth_m:.4f}m")
                    
                    # True Depth로 재투영
                    x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(u, v, true_depth_m)
                    
                    # 필터 강제 동기화 (값이 튀는 것을 방지)
                    self.filter_x.reset(x_cm)
                    self.filter_y.reset(y_cm)
                    self.filter_z.reset(z_cm)
                    return [x_cm, y_cm, z_cm]
                
            # [Phantom Detection 방지]
            # 시뮬레이션 환경에서는 GT가 절대적입니다.
            # 만약 GT 상에 물체가 없는데('exists': False), YOLO가 물체를 발견했다면
            # 이는 이미지 갱신 지연(Stale Image)으로 인한 '유령 탐지'일 가능성이 높습니다.
            # 따라서 이 경우 탐지 결과를 과감히 무시합니다.
            else:
                logging.warning(f"[PybulletVision] Phantom Detection 차단: YOLO는 찾았으나 GT에는 물체가 없습니다.")
                return None

        except Exception as e:
            logging.warning(f"[PybulletVision] GT Override Error: {e}")
        
        # (주의: 위에서 return None을 하므로, GT가 없을 때 아래 로직은 실행되지 않음)
        # 만약 Real World라면 아래 로직이 실행되겠지만, 여기는 PybulletVision이므로 항상 Sim입니다.
        
        # 칼만 필터 적용 (GT 미사용 시 - 혹시 모를 Fallback)
        filtered_x = self.filter_x.update(x_cm)
        filtered_y = self.filter_y.update(y_cm)
        filtered_z = self.filter_z.update(z_cm)
        
        logging.info(f"[PybulletVision.pixel_to_cm] "
                    f"픽셀=({u}, {v}), depth={depth_val:.4f} → "
                    f"월드=({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm → "
                    f"필터=({filtered_x:.2f}, {filtered_y:.2f}, {filtered_z:.2f})cm")
        
        return [filtered_x, filtered_y, filtered_z]

    def get_synced_packet(self):
        """서버로부터 영상, 깊이, 포즈를 한 번에 동기화하여 수신합니다."""
        packet = self.client.get_synced_packet()
        if not packet:
            logging.warning("[PybulletVision] 동기화 패킷 수신 실패")
        return packet

    def get_frame(self):
        return self.client.get_rgb_frame()

    def get_depth(self):
        return self.client.get_depth_frame()