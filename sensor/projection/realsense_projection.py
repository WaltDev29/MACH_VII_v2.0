"""
Intel RealSense 픽셀→3D 좌표 변환

RealSense SDK의 정확한 역투영 함수를 사용합니다.
"""

import logging
from typing import Tuple


def pixel_to_3d(pixel_x: int, pixel_y: int, depth_m: float, intrinsics) -> Tuple[float, float, float]:
    """
    RealSense 픽셀 좌표를 3D 카메라 좌표(cm)로 변환합니다.
    
    Args:
        pixel_x: 픽셀 X 좌표
        pixel_y: 픽셀 Y 좌표
        depth_m: 실제 깊이 (미터)
        intrinsics: RealSense intrinsics 객체
    
    Returns:
        (x, y, z): 카메라 좌표 cm 단위
    """
    try:
        import pyrealsense2 as rs
        
        # RealSense SDK의 정확한 역투영 사용
        point_m = rs.rs2_deproject_pixel_to_point(intrinsics, [pixel_x, pixel_y], depth_m)
        
        # m → cm 변환
        x_cm = point_m[0] * 100
        y_cm = point_m[1] * 100
        z_cm = point_m[2] * 100
        
        logging.debug(f"[RealSenseProjection] 픽셀({pixel_x}, {pixel_y}), depth={depth_m:.4f}m → "
                     f"카메라=({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")
        
        return x_cm, y_cm, z_cm
        
    except ImportError:
        logging.error("[RealSenseProjection] pyrealsense2 모듈을 찾을 수 없습니다!")
        return 0.0, 0.0, 0.0
    except Exception as e:
        logging.error(f"[RealSenseProjection] 변환 오류: {e}")
        return 0.0, 0.0, 0.0
