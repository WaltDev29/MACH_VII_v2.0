# test.py

import cv2
import requests
import json
import threading
import time
import numpy as np
import websocket
import sys
from shared.ui_dto import (
    UserRequestDTO, UserRequestType, SystemConfigurationDTO, 
    RobotTarget, CameraSource, OperationMode
)

# 서버 설정
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class MachTermClient:
    def __init__(self):
        self.running = True
        self.latest_emotion = "IDLE"
        self.current_config = SystemConfigurationDTO(
            target_robot=RobotTarget.VIRTUAL,
            active_camera=CameraSource.VIRTUAL,
            op_mode=OperationMode.RULE_BASED
        )
        self.mode = "MENU" # MENU or CHAT
        
    def video_stream_thread(self):
        """MJPEG 스트림을 수신하여 표시합니다 (interface/api_server.py의 스트리밍 엔드포인트 가정)"""
        # 참고: 현재 api_server.py에는 비디오 엔드포인트가 명시적이지 않을 수 있으나 
        # realsense_driver나 sim_client의 제너레이터를 사용할 수 있습니다.
        # 여기서는 UI 구성에 집중하여 비디오는 연결 시도만 합니다.
        pass

    def ws_listener_thread(self):
        """실시간 상태 및 사고 과정 수신"""
        def on_message(ws, message):
            data = json.loads(message)
            # 사고 과정(Thought) 출력
            thought = data.get("last_thought")
            if thought:
                print(f"\r\033[92m[BRAIN]\033[0m {thought}\n\033[94m[CHAT]\033[0m >> ", end="", flush=True)

        ws = websocket.WebSocketApp(WS_URL, on_message=on_message)
        ws.run_forever()

    def show_menu(self):
        """설정 선택 메뉴 표시"""
        print("\n" + "="*50)
        print("   🤖 MACH-VII v2.0 Terminal Setup")
        print("="*50)
        
        # 1. 로봇 선택
        print("\n[1] 로봇 대상 (Robot Target)")
        print(f"   1. Virtual (PyBullet) {'<--' if self.current_config.target_robot == RobotTarget.VIRTUAL else ''}")
        print(f"   2. Physical (Dofbot) {'<--' if self.current_config.target_robot == RobotTarget.PHYSICAL else ''}")
        
        # 2. 카메라 선택
        print("\n[2] 카메라 소스 (Camera Source)")
        print(f"   1. Virtual (PyBullet) {'<--' if self.current_config.active_camera == CameraSource.VIRTUAL else ''}")
        print(f"   2. Real (RealSense) {'<--' if self.current_config.active_camera == CameraSource.REAL else ''}")
        
        # 3. 사고 모드 선택
        print("\n[3] 사고 방식 (Operation Mode)")
        print(f"   1. Rule-Based {'<--' if self.current_config.op_mode == OperationMode.RULE_BASED else ''}")
        print(f"   2. Memory-Based (LLM) {'<--' if self.current_config.op_mode == OperationMode.MEMORY_BASED else ''}")
        
        print("\n" + "-"*50)
        print("   S. 설정 적용 및 채팅 시작")
        print("   Q. 종료")
        print("-"*50)

    def send_config(self):
        """현재 설정을 서버에 전송"""
        print(f"\n[System] 설정 적용 중: {self.current_config.dict()}")
        req = UserRequestDTO(
            request_type=UserRequestType.CONFIG_CHANGE,
            config=self.current_config
        )
        try:
            res = requests.post(f"{SERVER_URL}/api/request", json=req.dict())
            if res.status_code == 200:
                print("✅ 설정이 성공적으로 업데이트되었습니다.")
                return True
            else:
                print(f"❌ 설정 업데이트 실패: {res.text}")
        except Exception as e:
            print(f"❌ 서버 연결 오류: {e}")
        return False

    def send_command(self, text):
        """자연어 명령 전송"""
        req = UserRequestDTO(
            request_type=UserRequestType.COMMAND,
            command=text
        )
        try:
            requests.post(f"{SERVER_URL}/api/request", json=req.dict())
        except Exception as e:
            print(f"\n❌ 명령 전송 실패: {e}")

    def run(self):
        # WS 리스너 시작
        threading.Thread(target=self.ws_listener_thread, daemon=True).start()

        while self.running:
            if self.mode == "MENU":
                self.show_menu()
                choice = input("\n선택 (번호): ").lower()
                
                if choice == '1':
                    sub = input(" 로봇 (1. 가상, 2. 실물): ")
                    self.current_config.target_robot = RobotTarget.VIRTUAL if sub == '1' else RobotTarget.PHYSICAL
                elif choice == '2':
                    sub = input(" 카메라 (1. 가상, 2. 실물): ")
                    self.current_config.active_camera = CameraSource.VIRTUAL if sub == '1' else CameraSource.REAL
                elif choice == '3':
                    sub = input(" 모드 (1. 규칙, 2. 메모리): ")
                    self.current_config.op_mode = OperationMode.RULE_BASED if sub == '1' else OperationMode.MEMORY_BASED
                elif choice == 's':
                    if self.send_config():
                        self.mode = "CHAT"
                        print("\n" + "*"*50)
                        print("   채팅 모드에 진입했습니다.")
                        print("   - 메뉴로 돌아가려면 '0' 입력")
                        print("   - 종료하려면 'q' 입력")
                        print("*"*50 + "\n")
                elif choice == 'q':
                    self.running = False
                
            elif self.mode == "CHAT":
                cmd = input("\033[94m[CHAT]\033[0m >> ")
                if cmd.lower() == 'q':
                    self.running = False
                elif cmd == '0':
                    self.mode = "MENU"
                elif cmd.strip():
                    self.send_command(cmd)

        print("\n테스트 클라이언트를 종료합니다.")

if __name__ == "__main__":
    client = MachTermClient()
    client.run()
