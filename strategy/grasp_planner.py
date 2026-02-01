# strategy/grasp_planner.py

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

class GraspPlanner:
    """
    GPD (Grasp Pose Detection) - 물체의 그립 자세를 계산하는 클래스
    
    클라우드 포인트 기반 그립 자세 생성 (규칙 기반 + 메모리 기반 하이브리드)
    """
    
    def __init__(self):
        # 로봇 그리퍼 사양 (PyBullet DOFbot)
        self.GRIPPER_MAX_WIDTH_CM = 6.0 # 최대 개방 6cm
        
        # 카메라 파라미터 (근사값)
        self.FOCAL_LENGTH_PX = 520.0 # FX, FY 근사값
        
        # 물체별 최적 그립 오프셋 메모리 (학습 가능)
        self.grasp_memory = {
            "bottle": {"approach_offset_z": 5.0, "gripper_width": 80.0}, # % 단위
            "cup": {"approach_offset_z": 5.0, "gripper_width": 90.0},
            "teddy": {"approach_offset_z": 8.0, "gripper_width": 100.0},
            "duck": {"approach_offset_z": 5.0, "gripper_width": 80.0},
            "soccerball": {"approach_offset_z": 10.0, "gripper_width": 100.0},
            "default": {"approach_offset_z": 5.0, "gripper_width": 80.0}
        }
    
    def compute_grasp_pose(self, 
                          object_name: str, 
                          object_position: Dict[str, float],
                          bbox: Tuple[int, int] = (0, 0),
                          depth_map: Optional[np.ndarray] = None) -> Dict[str, any]:
        """
        물체의 그립 자세를 계산합니다. (범용 GPD 로직 적용)
        그리퍼 사양(최대 6cm)을 고려하여 계산합니다.
        
        Args:
            object_name: 물체 이름
            object_position: 물체 중심 좌표 {x, y, z} (cm)
            bbox: 바운딩 박스 크기 (w, h) 픽셀
            
        Returns:
            grasp_pose: {
                "pre_grasp": {x, y, z},  # 접근 위치
                "grasp": {x, y, z},       # 잡기 위치
                "gripper_width": float     # 그리퍼 개방 정도 (%)
            }
        """
        # 1. 물체 실제 크기 추정 (Pinhole Model 역산)
        # Bbox Width(px) * Depth(cm) / FocalLength(px) = Width(cm)
        # object_position['x']는 로봇 베이스 기준 좌표이므로 깊이(z)는 아님.
        # 하지만 VisionBridge에서 변환된 좌표계에서 Z는 높이이고 X가 깊이 방향(전방).
        # PyBullet 좌표계: X:앞+, Y:왼쪽+, Z:위+
        # 카메라 좌표계에서의 Depth는 Robot X 좌표와 유사함 (카메라가 로봇 뒤/위에 있다면)
        # 하지만 정확한 Depth는 VisionBridge에서 이미 World 좌표로 변환되어 소실됨.
        # 대략적으로 카메라 높이와 물체 거리를 통해 추정하거나, bbox 픽셀만으로 안전마진 설정.
        
        # 여기서는 가장 보수적으로 "최대 개방"을 기본으로 하되, 
        # 메모리에 값이 있으면 그걸 씁니다.
        
        approach_offset_z = 10.0
        gripper_percent = 100.0 # 기본 100% 개방
        grasp_depth_offset = -3.0
        
        # 메모리 조회
        memory_params = self.grasp_memory.get(object_name)
        
        if memory_params:
            approach_offset_z = memory_params["approach_offset_z"]
            gripper_percent = memory_params["gripper_width"]
        else:
            # [범용 로직]
            logging.info(f"[GraspPlanner] '{object_name}' - 새로운 물체, 범용 GPD 로직 적용")
            
            # (1) 물체 크기 추정 및 파지 전략 수립
            grasp_pos_x_offset = 0.0
            
            if bbox[0] > 0 and bbox[1] > 0:
                # 간단한 가정: 화면 중앙 물체 거리 약 50cm 가정
                est_dist_cm = 50.0 
                # 너비(w)와 높이(h) 추정
                est_w_cm = (bbox[0] / self.FOCAL_LENGTH_PX) * est_dist_cm
                est_h_cm = (bbox[1] / self.FOCAL_LENGTH_PX) * est_dist_cm
                
                logging.info(f"[GraspPlanner] 물체 크기 추정: W={est_w_cm:.1f}cm, H={est_h_cm:.1f}cm")
                
                min_dim = min(est_w_cm, est_h_cm)
                
                if min_dim > self.GRIPPER_MAX_WIDTH_CM:
                    logging.warning(f"[GraspPlanner] ⚠️ 물체가 너무 큽니다 (Min Dim {min_dim:.1f}cm > {self.GRIPPER_MAX_WIDTH_CM}cm).")
                    
                    # [전략: 가장자리 잡기 Edge Grasp]
                    # 물체가 너무 크면 중심을 잡을 수 없으므로, 오른쪽 가장자리를 공략
                    # 실제로는 물체 형상을 알아야 하지만, 여기서는 Bbox 우측 끝에서 1.5cm 안쪽을 잡음
                    # (회전이 가능하다면 짧은 축을 잡겠지만, 현재는 위치 이동만 가능하므로 X축 이동 시도)
                    
                    edge_offset = (est_w_cm / 2.0) - 1.5 # 중심에서 우측으로 이동
                    grasp_pos_x_offset = edge_offset
                    
                    logging.info(f"[GraspPlanner] 💡 전략 변경: 가장자리 잡기 (Offset X +{edge_offset:.1f}cm)")
                    
                    gripper_percent = 60.0 # 입구/가장자리는 보통 얇으므로 적당히 벌림
                    grasp_depth_offset = -2.0 # 가장자리는 깊지 않게
                    
                else:
                    # 크기 적절함. 폭에 맞춰 그리퍼 조절
                    target_width = min_dim + 2.0
                    gripper_percent = (target_width / self.GRIPPER_MAX_WIDTH_CM) * 100.0
                    gripper_percent = max(min(gripper_percent, 100.0), 40.0)
                    
                    if est_h_cm < est_w_cm and est_w_cm > self.GRIPPER_MAX_WIDTH_CM:
                        logging.info("[GraspPlanner] 💡 90도 회전 필요 (세로로 잡아야 함) - *현재 회전 미지원*")

            
            # (2) 물체별 휴리스틱 보정
            if "kite" in object_name.lower():
                 # 얇은 물체는 바닥에 붙어있으므로 덜 내려가야 함
                 grasp_depth_offset = -0.5 
                 approach_offset_z = 8.0
            
            
        # 3. 좌표 계산
        # 접근 위치 (Pre-grasp): 물체 표면 + 접근 오프셋 + X축 오프셋(Edge)
        pre_grasp_pos = {
            "x": object_position["x"] + grasp_pos_x_offset, # 카메라 기준 X는 로봇 기준 X (PyBullet)
            "y": object_position["y"],
            "z": object_position["z"] + approach_offset_z
        }
        
        # 잡기 위치 (Grasp): 물체 표면 + 잡기 깊이 + X축 오프셋(Edge)
        grasp_pos = {
            "x": object_position["x"] + grasp_pos_x_offset,
            "y": object_position["y"],
            "z": object_position["z"] + grasp_depth_offset
        }
        
        # 4. 그리퍼 개방 정도
        gripper_open_percent = min(gripper_percent, 100.0)
        
        grasp_pose = {
            "pre_grasp": pre_grasp_pos,
            "grasp": grasp_pos,
            "gripper_width": gripper_open_percent,
            "object_name": object_name
        }
        
        logging.info(f"[GraspPlanner] {object_name} 그립 자세: "
                    f"접근={pre_grasp_pos['x']:.1f}, {pre_grasp_pos['y']:.1f}, {pre_grasp_pos['z']:.1f} (Offset X {grasp_pos_x_offset:.1f})")
        
        return grasp_pose
    
    def update_grasp_memory(self, object_name: str, success: bool, params: Dict):
        """
        그립 성공/실패에 따라 메모리를 업데이트합니다 (학습)
        
        Args:
            object_name: 물체 이름
            success: 그립 성공 여부
            params: 사용한 그립 파라미터
        """
        if success:
            logging.info(f"[GraspPlanner] {object_name} 그립 성공! 파라미터 저장.")
            self.grasp_memory[object_name] = params
        else:
            logging.warning(f"[GraspPlanner] {object_name} 그립 실패. 파라미터 조정 필요.")
            # TODO: 실패 시 파라미터 자동 조정 로직


# 싱글톤 인스턴스
grasp_planner = GraspPlanner()
