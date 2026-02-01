# embodiment/pybullet_robot.py

import logging
import time  # 동기 모드를 위해 필요
import threading
from .robot_base import RobotBase
from interface.backend.sim_client import pybullet_client

class PybulletRobot(RobotBase):
    """
    파이불렛 시뮬레이터와 통신하여 로봇을 제어하는 실제 구현 클래스입니다.
    """
    def __init__(self, server_url="http://localhost:5000"):
        super().__init__()
        self.server_url = server_url
        self.stop_event = threading.Event()

    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50, wait_arrival: bool = False, timeout: float = 5.0) -> bool:
        """
        로봇 베이스 기준 cm 좌표를 받아 PyBullet에 m 단위로 전송합니다.
        
        Args:
            x, y, z: 로봇 베이스 좌표계의 cm 단위 좌표
            speed: 이동 속도 (0~100)
            wait_arrival: True면 도착할 때까지 대기 (동기 모드)
            timeout: 도착 대기 최대 시간 (초)
        """
        try:
            if not pybullet_client.connected:
                 raise ConnectionError("PyBullet Server Disconnected")
                 
            # cm → m 변환
            pos_m = [x / 100.0, y / 100.0, z / 100.0]
            
            logging.info(f"[PybulletRobot] 이동 명령: ({x:.1f}, {y:.1f}, {z:.1f})cm "
                        f"→ PyBullet: ({pos_m[0]:.3f}, {pos_m[1]:.3f}, {pos_m[2]:.3f})m @ speed={speed} "
                        f"({'SYNC' if wait_arrival else 'ASYNC'})")
            
            # WebSocket으로 명령 전송
            pybullet_client.set_pos(pos_m)
            
            # 상태 업데이트
            self.current_state["position"] = {"x": x, "y": y, "z": z}
            
            # 동기 모드: 도착할 때까지 대기
            if wait_arrival:
                self.stop_event.clear() # 대기 시작 전 초기화 (주의: 여러 스레드가 동시에 move하면 꼬일 수 있음. 현재는 단일 스레드 가정)
                
                arrival_threshold = 1.0  # 1cm 이내면 도착 판정
                start_time = time.time()
                
                while (time.time() - start_time) < timeout:
                    if self.stop_event.is_set():
                        logging.warning("[PybulletRobot] 이동 중 강제 중단됨!")
                        return False
                        
                    current_pos = self.get_current_pose()
                    
                    dx = abs(current_pos['x'] - x)
                    dy = abs(current_pos['y'] - y)
                    dz = abs(current_pos['z'] - z)
                    total_error = (dx**2 + dy**2 + dz**2) ** 0.5
                    
                    if total_error < arrival_threshold:
                        logging.info(f"[PybulletRobot] 도착 완료! (오차: {total_error:.2f}cm)")
                        return True
                    
                    time.sleep(0.02)  # 50Hz 체크
                
                logging.warning(f"[PybulletRobot] 도착 타임아웃 ({timeout}초)")
                return False
            
            logging.debug(f"[PybulletRobot] WebSocket 전송 완료 - connected: {pybullet_client.connected}")
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 이동 실패: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False

    def move_gripper(self, open_percent: float) -> bool:
        """
        그리퍼의 개폐 정도를 제어합니다 (0: 닫힘, 100: 열림).
        """
        try:
            # open_percent(0~100) -> 0.0 ~ 0.06 m 변환
            # PyBullet 규격: 0.0(닫힘), 0.06(최대 열림)
            val = (open_percent / 100.0) * 0.06
            logging.info(f"[PybulletRobot] 그리퍼 동작: {open_percent:.1f}% ({'열림' if open_percent > 50 else '닫힘'})")
            pybullet_client.set_gripper(val)
            self.current_state["gripper"] = open_percent
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 그리퍼 동작 실패: {e}")
            return False
        
    def set_force(self, force: float) -> bool:
        """
        로봇의 모터 및 그리퍼 구동 힘을 설정합니다.
        Args:
            force: 힘의 크기 (단위: N 또는 시뮬레이션 단위)
        """
        try:
            pybullet_client.set_force(force)
            logging.info(f"[PybulletRobot] 구동 힘 설정: {force}")
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 힘 설정 실패: {e}")
            return False

    def get_current_pose(self) -> dict:
        """
        현재 로봇 손끝(End-effector)의 cm 좌표를 PyBullet 서버로부터 가져옵니다.
        """
        if not pybullet_client.connected:
             raise ConnectionError("PyBullet Server Disconnected")
             
        # pybullet_client가 실시간 수신하는 최신 상태 반환
        with pybullet_client.lock:
            state = pybullet_client.latest_state.get('robot', {})
        
        pos = state.get('ee', {})
        
        # m → cm 변환
        result = {
            "x": pos.get('x', 0) * 100.0,
            "y": pos.get('y', 0) * 100.0,
            "z": pos.get('z', 0) * 100.0
        }
        
        logging.debug(f"[PybulletRobot] get_current_pose: PyBullet=({pos.get('x', 0):.3f}, "
                    f"{pos.get('y', 0):.3f}, {pos.get('z', 0):.3f})m "
                    f"→ ({result['x']:.1f}, {result['y']:.1f}, {result['z']:.1f})cm")
        return result

    def get_gripper_ratio(self) -> float:
        """
        현재 그리퍼의 개폐 상태를 반환합니다.
        Return: 0.0 (완전 닫힘) ~ 1.0 (완전 열림)
        """
        with pybullet_client.lock:
            state = pybullet_client.latest_state.get('robot', {})
        
        # PyBullet 서버가 gripper 값을 0.0~0.06(m)으로 보낸다고 가정
        # 안 보내면 None일 수 있음. 기본값 0 (닫힘)
        val = state.get('gripper', 0.0)
        
        # 0.0 ~ 0.06 -> 0.0 ~ 1.0 정규화
        ratio = val / 0.06
        return max(0.0, min(1.0, ratio))

    def set_joints(self, angles: list, speed: int = 50) -> bool:
        """
        5개 관절의 각도를 직접 제어합니다.
        """
        try:
            logging.info(f"[PybulletRobot] 관절 각도 설정: {[f'{a:.1f}°' for a in angles]} @ speed={speed}")
            pybullet_client.set_joints(angles)
            self.current_state["joints"] = angles
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 관절 제어 실패: {e}")
            return False

    def emergency_stop(self):
        """
        위급 상황 시 로봇의 모든 구동을 즉시 중단합니다.
        """
        logging.warning("[PybulletRobot] ⚠️  긴급 정지 발동!")
        self.stop_event.set()
        try:
            # 1. 명령 전송 중단
            pybullet_client.current_target_pos = None
            
            # 2. 상태 플래그 업데이트
            self.current_state["is_moving"] = False
            
            logging.info("[PybulletRobot] 긴급 정지 완료 - 명령 전송 중단")
        except Exception as e:
            logging.error(f"[PybulletRobot] 긴급 정지 실패: {e}")