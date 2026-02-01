import socketio
import threading
import time
import requests
import logging
from shared.config import GlobalConfig

class PyBulletClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PyBulletClient, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized: return
        self.sio = socketio.Client()
        self.server_url = GlobalConfig.SIM_SERVER_URL
        self.connected = False
        self.latest_state = {}
        self.lock = threading.Lock()
        
        # Callbacks
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('robot_state', self.on_robot_state)
        self.sio.on('object_state', self.on_object_state)
        
        self.initialized = True
        
        # 재전송 로직 제거: Visual Servoing이 20Hz로 직접 제어하므로 불필요



    def connect(self, timeout=2):
        if self.connected: return
        try:
            logging.info(f"[PyBullet] Connecting to {self.server_url} (timeout={timeout}s)...")
            # wait=True와 wait_timeout을 사용하여 연결 시도를 제어
            self.sio.connect(self.server_url, wait_timeout=timeout)
            self.connected = True
        except Exception as e:
            if "Client is not in a disconnected state" in str(e):
                logging.info("[PyBullet] 이미 연결된 상태입니다. (Flag 보정)")
                self.connected = True
            else:
                logging.error(f"[PyBullet] Connection failed: {e}")
                logging.warning("[PyBullet] 시뮬레이션 서버가 실행 중인지 확인하세요. (기본값: http://localhost:5000)")
                self.connected = False

    def on_connect(self):
        logging.info("[PyBullet] 시뮬레이션 서버에 연결되었습니다.")
        self.connected = True

    def on_disconnect(self):
        logging.info("[PyBullet] 연결이 끊어졌습니다.")
        self.connected = False

    def on_robot_state(self, data):
        with self.lock:
            self.latest_state['robot'] = data

    def on_object_state(self, data):
        with self.lock:
            self.latest_state['object'] = data

    # README 프로토콜과 일치하는 명령 메서드
    
    def set_joints(self, joints: list):
        if not self.connected: return
        self.sio.emit('set_joints', {'joints': joints})

    def set_force(self, force: float):
        """ 로봇 모터/그리퍼 힘 설정 """
        if not self.connected: return
        self.sio.emit('set_force', {'force': force})

    def set_pos(self, pos: list):
        """ pos: [x, y, z] - 단일 전송만 수행 """
        if not self.connected: return
        self.sio.emit('set_pos', {'pos': pos})

    def set_gripper(self, value: float):
        """ value: 0.0 ~ 0.06 (미터 단위 개폐량) """
        if not self.connected: return
        self.sio.emit('set_gripper', {'gripper': value})

    def set_object(self, op="create", obj_type="duck", fix=False):
        """ 시뮬레이션 환경에 물체를 생성하거나 조작합니다. """
        if not self.connected: return
        self.sio.emit('set_object', {'op': op, 'object': obj_type, 'fix': fix})

    # 비디오 프록시 (MJPEG)
    def get_video_stream(self):
        """ PyBullet 비디오 스트림을 위한 제너레이터 (프록시) """
        try:
            # PyBullet MJPEG 스트림에 연결하여 청크 단위로 반환
            resp = requests.get(f"{self.server_url}/", stream=True, timeout=5)
            for chunk in resp.iter_content(chunk_size=1024):
                yield chunk
        except Exception as e:
            logging.error(f"[PyBullet] Video Proxy Error: {e}")
            # Yield error frame or stop
            return

    def get_synced_packet(self):
        """
        [Layer 1] 서버로부터 동기화된 영상, 뎁스, 포즈 데이터를 가져옵니다.
        PyBullet 서버의 실제 엔드포인트 사용: /image (JPEG), /depth (JSON), robot_state (WebSocket)
        """
        if not self.connected:
            logging.debug("[PyBulletClient] 서버에 연결되지 않음, WebSocket 연결 시도...")
            self.connect()
            if not self.connected:
                return None
            
        try:
            import numpy as np
            import cv2
            
            # 1. HTTP로 컬러 이미지 가져오기 (/image) - JPEG 형식
            img_resp = requests.get(f"{self.server_url}/image", timeout=3.0)
            if img_resp.status_code != 200:
                logging.error(f"[PyBulletClient] /image 요청 실패: {img_resp.status_code}")
                return None
            
            # JPEG 바이트를 numpy 배열로 변환
            img_array = np.frombuffer(img_resp.content, dtype=np.uint8)
            color_frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if color_frame is None:
                logging.error("[PyBulletClient] 이미지 디코딩 실패")
                return None
            
            # 2. HTTP로 깊이 데이터 가져오기 (/depth) - JSON 형식
            # 주의: JSON 형식이라 용량이 큼 (600x480 배열) - 타임아웃 여유있게 설정
            depth_resp = requests.get(f"{self.server_url}/depth", timeout=5.0)
            if depth_resp.status_code != 200:
                logging.error(f"[PyBulletClient] /depth 요청 실패: {depth_resp.status_code}")
                return None
            
            # JSON을 numpy 배열로 변환
            depth_list = depth_resp.json()
            depth_frame = np.array(depth_list, dtype=np.float32)
            
            # 3. WebSocket으로 수신한 최신 robot_state 가져오기
            with self.lock:
                robot_state = self.latest_state.get('robot', {})
                
            # 4. 동기화된 패킷 구성
            packet = {
                "color": color_frame,
                "depth": depth_frame,
                "captured_pose": robot_state.get('ee', {})  # 엔드이펙터 위치
            }
            
            logging.debug(f"[PyBulletClient] 패킷 생성됨 - color: {color_frame.shape}, depth: {depth_frame.shape}")
            return packet
            
        except Exception as e:
            logging.error(f"[PyBulletClient] get_synced_packet 오류: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

    def get_rgb_frame(self):
        packet = self.get_synced_packet()
        return packet.get("color") if packet else None

    def get_depth_frame(self):
        packet = self.get_synced_packet()
        return packet.get("depth") if packet else None

pybullet_client = PyBulletClient()