from abc import ABC, abstractmethod
from typing import List, Optional
from shared.filters import KalmanFilter

class VisionBase(ABC):
    """
    비전 시스템의 공통 인터페이스입니다.
    2D 픽셀 좌표와 깊이(Depth) 정보를 3D 좌표로 변환하는 규격을 정의합니다.
    """

    def __init__(self):
        """
        카메라 내인자(Intrinsics)와 3D 좌표 정제용 필터를 초기화합니다.
        """
        # 카메라 내부 파라미터 (Subclass에서 실제 값으로 갱신 필요)
        self.fx, self.fy = 0.0, 0.0
        self.cx, self.cy = 0.0, 0.0
        
        # 3D 공간 좌표(x, y, z) 떨림 방지를 위한 칼만 필터
        self.filter_x = KalmanFilter()
        self.filter_y = KalmanFilter()
        self.filter_z = KalmanFilter()

    def set_intrinsics(self, fx: float, fy: float, cx: float, cy: float):
        """
        카메라의 내인자 값을 설정합니다.
        """
        self.fx, self.fy = fx, fy
        self.cx, self.cy = cx, cy

    def pixel_to_cm(self, u: float, v: float, depth_m: float) -> Optional[List[float]]:
        """
        픽셀 좌표를 3D cm 좌표로 변환합니다.
        V1.0의 비례 계산 방식을 사용하여 카메라 회전을 자동 보정합니다.
        """
        if depth_m <= 0:
            return None

        # PyBullet 카메라 설정값
        WIDTH, HEIGHT = 600, 480
        
        # V1.0 방식: 비례식 기반 좌표 변환 (Simplified Pinhole Model)
        # 복잡한 역행렬 연산 없이, 깊이(z)와 화면 중심으로부터의 거리 비례를 이용해 x, y를 추정합니다.
        # 가정: 카메라가 물체를 정면으로 바라보고 있으며, 렌즈 왜곡이 없다고 가정합니다.
        # 공식: 실제_길이 / 실제_거리 = 픽셀_길이 / 화면_폭_상수
        z_cm = depth_m * 100.0  # 단위 변환: m -> cm
        x_cm = (u - WIDTH / 2) * (z_cm / WIDTH) # X축 편차 비례 계산
        y_cm = (v - HEIGHT / 2) * (z_cm / HEIGHT) # Y축 편차 비례 계산

        # 3D 좌표에 칼만 필터 적용
        filtered_x = self.filter_x.update(x_cm)
        filtered_y = self.filter_y.update(y_cm)
        filtered_z = self.filter_z.update(z_cm)
        
        import logging
        logging.info(f"[VisionBase.pixel_to_cm] "
                    f"픽셀=({u}, {v}), depth={depth_m:.4f}m → "
                    f"비례계산=({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm → "
                    f"필터=({filtered_x:.2f}, {filtered_y:.2f}, {filtered_z:.2f})cm")

        return [filtered_x, filtered_y, filtered_z]

    @abstractmethod
    def get_frame(self):
        """실제 영상 및 깊이 데이터를 획득하는 추상 메서드입니다."""
        pass