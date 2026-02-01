# embodiment/robot_factory.py

import logging
from shared.config import GlobalConfig

class RobotFactory:
    """
    전역 설정(SIM_MODE)에 맞는 로봇 드라이버 인스턴스를 생성하여 반환합니다.
    연결 실패 시 예외를 발생시킵니다.
    """
    _instance = None

    @staticmethod
    def get_robot():
        """
        설정된 모드에 따라 로봇 드라이버를 반환합니다.
        """
        if GlobalConfig.SIM_MODE:
            try:
                from .pybullet_robot import PybulletRobot
                robot = PybulletRobot()
                logging.info("[RobotFactory] PybulletRobot 초기화 성공")
                return robot
            except Exception as e:
                logging.error(f"[RobotFactory] PybulletRobot 초기화 실패: {e}")
                raise RuntimeError(f"가상 로봇 연결 실패: {e}")
        
        # 실물 로봇(Dofbot) 드라이버
        try:
            from .dofbot_robot import DofbotRobot
            robot = DofbotRobot()
            logging.info("[RobotFactory] DofbotRobot 초기화 성공")
            return robot
        except Exception as e:
            logging.error(f"[RobotFactory] DofbotRobot 초기화 실패: {e}")
            raise RuntimeError(f"실물 로봇 연결 실패: {e}")