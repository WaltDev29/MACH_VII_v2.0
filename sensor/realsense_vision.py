# sensor/realsense_vision.py

import numpy as np
from .vision_base import VisionBase
from .realsense_driver import realsense_driver

class RealSenseVision(VisionBase):
    """
    실물 RealSense 카메라를 위한 비전 구현체입니다.
    """
    def __init__(self):
        super().__init__()
        # 하드웨어 드라이버 시작
        realsense_driver.start()

    def get_synced_packet(self):
        """
        RGB, Depth, 그리고 해당 시점의 로봇 포즈를 정합하여 반환합니다.
        """
        color, depth = realsense_driver.get_frames()
        if color is None or depth is None:
            return None
            
        # [Sync] 영상 획득 시점의 로봇 포즈 획득
        # 실물 로봇의 경우 드라이버로부터 현재 관절/좌표를 읽어와야 함
        # NOTE: 직접 robot_controller를 import하지 않고 state를 통해 간접 참조
        from state.system_state import system_state
        pose = {}
        
        # 로봇 상태에서 포즈 정보가 있다면 사용 (추후 확장 가능)
        # 현재는 빈 딕셔너리로 유지 (실제 하드웨어 연동 시 드라이버에서 직접 읽어야 함)

        return {
            "color": color,
            "depth": depth,
            "captured_pose": pose
        }

    def get_frame(self):
        """
        현재 프레임(Color, Depth)을 반환합니다.
        VisionBase의 추상 메서드 구현입니다.
        """
        return realsense_driver.get_frames()

    def pixel_to_cm(self, u: int, v: int, depth_val: float) -> list:
        """
        픽셀 좌표와 깊이 값을 기반으로 카메라 기준 3D 좌표(x, y, z)를 계산합니다.
        Intel RealSense SDK의 내장 함수를 사용하거나 근사치를 계산합니다.
        """
        # 단위 변환: depth_val (m) -> cm
        # 단순 핀홀 모델 근사 (추후 카메라 내부 파라미터 적용 필요)
        fx, fy = 600, 600 # 임시 초점 거리
        cx, cy = 320, 240 # 이미지 중심
        
        z = depth_val * 100.0 # m to cm
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        
        return [x, y, z]
