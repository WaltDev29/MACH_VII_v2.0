import numpy as np
import logging
from ..core import VisionBase
from interface.backend.sim_client import pybullet_client
from sensor.projection import pybullet_projection

class PybulletVision(VisionBase):
    """
    [Layer 1: Sensor Implementation] PyBullet 시뮬레이터 전용 비전 구현체입니다.
    
    물리 엔진의 Ground Truth(그라운드 트루스: 물리 엔진이 알고 있는 실제 참값) 데이터와 시뮬레이션 카메라의 영상을 결합하여 
    오차 없는 정밀한 비전 데이터를 제공하며, 'Oracle Depth(오라클 뎁스: 오차 없는 완벽한 깊이 데이터)' 기능을 지원합니다.
    """
    def __init__(self):
        """
        시뮬레이션 클라이언트를 연결하고 시뮬레이션 특화 파라미터를 설정합니다.
        """
        super().__init__()
        
        # 1. 시뮬레이션 클라이언트 싱글톤(단일 인스턴스) 연결
        self.client = pybullet_client
        if not self.client.connected:
            self.client.connect()
        
        logging.info("[PybulletVision] 시뮬레이션 특화 비전 시스템이 활성화되었습니다.")

        # 2. [Polymorphism: 다형성 - 같은 기능을 환경에 맞게 다르게 구현] 시뮬레이션 필터 튜닝
        # 시뮬레이션 환경은 노이즈가 거의 없으므로 측정값을 강하게 신뢰하도록 튜닝합니다.
        # Process Variance(프로세스 공분산: 시스템 변화량)를 낮추고 
        # Measurement Variance(측정 공분산: 센서 노이즈량)를 높여 반응 속도를 극대화합니다.
        from shared.filters import KalmanFilter
        self.filter_x = KalmanFilter(process_variance=1e-3, measurement_variance=1e-4)
        self.filter_y = KalmanFilter(process_variance=1e-3, measurement_variance=1e-4)
        self.filter_z = KalmanFilter(process_variance=1e-3, measurement_variance=1e-4)
        
    def pixel_to_local_cm(self, u: int, v: int, depth_val: float):
        """
        [New] 픽셀 좌표를 카메라 기준 3D 로컬 좌표(cm)로 변환합니다.
        월드 좌표계 변환 전의 순수 카메라 기준 위치가 필요할 때(예: 그리퍼 카메라) 사용합니다.
        """
        if depth_val <= 0:
            return None
            
        # [Helper] 로컬 뷰 좌표 반환
        return pybullet_projection.pixel_to_view_space(u, v, depth_val)

    def pixel_to_cm(self, u: int, v: int, depth_val: float):
        """
        [Override: 재정의] 시뮬레이션 특화 좌표 변환 및 보정 로직입니다.
        
        시뮬레이션 환경에서는 단순 비례식 대신 물리 엔진의 View/Projection Matrix(뷰/프로젝션 행렬: 3D 공간을 2D 화면으로 그리기 위한 수학적 변환 행렬) 기반 변환을 수행하며,
        'Oracle Depth(오라클 뎁스: 정답 깊이)' 알고리즘을 통해 픽셀 오차는 유지하되 깊이 오차만 제거합니다.
        """
        if depth_val <= 0:
            return None
        
        # 1. 기본 투영: PyBullet 전용 투영 모듈 사용
        x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(u, v, depth_val)
        
        # 2. [Sim Mode Correction] Ground Truth(그라운드 트루스: 실제 정답값) 기반 보정
        try:
            with self.client.lock:
                raw_obj = self.client.latest_state.get('object', {})
            
            gt_obj = raw_obj.get('object', raw_obj)
            
            # 물체가 존재하고 비전 결과와 근접(20cm 이내)한 경우에만 보정 수행
            if gt_obj.get('exists'):
                gt_x, gt_y, gt_z = gt_obj['x'] * 100.0, gt_obj['y'] * 100.0, gt_obj['z'] * 100.0
                dist_sq = (x_cm - gt_x)**2 + (y_cm - gt_y)**2 + (z_cm - gt_z)**2
                
                if dist_sq < 400.0: 
                    # [Oracle Depth(오라클 뎁스) 알고리즘]
                    # 원리: YOLO가 찾은 픽셀(u, v)과 GT(정답) 물체까지의 '정확한 평면 깊이'를 결합합니다.
                    # 효과: 인식 결과의 현장감은 살리되, 깊이 측정 노이즈로 인한 z축 튐 현상을 완벽히 방지합니다.
                    true_depth_m = pybullet_projection.calculate_planar_depth(gt_x, gt_y, gt_z)
                    x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(u, v, true_depth_m)
                    
                    # 필터 강제 동기화 (오차를 즉시 0으로 만듦)
                    self.filter_x.reset(x_cm); self.filter_y.reset(y_cm); self.filter_z.reset(z_cm)
                    return [x_cm, y_cm, z_cm]
                
            # [Phantom Detection(팬텀 디텍션: 유령 인식) 방지] 
            # GT(정답)에 물체가 없는데 비전이 물체를 찾았다면 이는 데이터 갱신 지연이므로 무시합니다.
            else:
                logging.warning("[PybulletVision] Phantom Detection 차단 (GT 물체 없음)")
                return None

        except Exception as e:
            logging.warning(f"[PybulletVision] GT 보정 실패: {e}")
        
        # 3. 필터 적용 (보정 미사용 시 대비)
        return [self.filter_x.update(x_cm), self.filter_y.update(y_cm), self.filter_z.update(z_cm)]

    def get_synced_packet(self):
        """
        시뮬레이션 서버로부터 영상, 깊이, 로봇 포즈를 동기화된 상태로 통합 수신합니다.
        """
        return self.client.get_synced_packet()

    def get_frame(self):
        """
        현재 시뮬레이션 화면(RGB)을 반환합니다.
        """
        return self.client.get_rgb_frame()

    def get_depth(self):
        """
        현재 시뮬레이션 깊이 지도를 반환합니다.
        """
        return self.client.get_depth_frame()

    def capture_gripper(self, include_depth: bool = True):
        """
        [Gripper Camera] 엔드 이펙터 카메라의 동기화된 패킷을 반환합니다.
        """
        return self.client.get_ee_synced_packet(include_depth=include_depth)

    def measure_focus_score(self, image) -> float:
        """
        이미지의 선명도를 측정합니다.
        시뮬레이션 환경은 항상 선명하므로 그저 100을 반환합니다.
        """
        return 100.0