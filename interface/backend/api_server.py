from fastapi import FastAPI, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time

from shared.pipeline import pipeline
from shared.state_broadcaster import broadcaster
from brain.logic_brain import logic_brain
from expression.emotion_controller import emotion_controller
from brain.emotion_updater import llm_updater
from sensor.realsense_driver import realsense_driver
from sensor.perception_manager import perception_manager
from interface.backend.sim_client import pybullet_client
from memory.falkordb_manager import memory_manager
from strategy.strategy_manager import strategy_manager
from shared.ui_dto import UserRequestDTO, UserRequestType, OperationMode, RobotTarget, CameraSource

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # 1. 하위 계층 드라이버 및 루프 시작
    perception_manager.start()
    emotion_controller.start()
    llm_updater.start()
    
    from embodiment.robot_controller import robot_controller
    robot_controller.start()
    
    # 2. [핵심] 파이프라인 컴포넌트 등록
    # 7단계 레이어 아키텍처의 인스턴스를 파이프라인에 연결합니다.
    pipeline.register_component("emotion_controller", emotion_controller)
    pipeline.register_component("robot_controller", robot_controller)
    pipeline.register_component("realsense_driver", realsense_driver)
    
    # 메모리 연결
    memory_manager.connect()

@app.on_event("shutdown")
async def shutdown_event():
    perception_manager.stop()
    emotion_controller.stop()
    llm_updater.stop()
    from embodiment.robot_controller import robot_controller
    robot_controller.stop()

@app.get("/")
def read_root():
    return {"status": "MACH_VII_v2.0 Online (Pipeline Active)"}

# WebSocket 엔드포인트: 파이프라인 기반 통합 스냅샷 스트리밍
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 파이프라인을 통해 정합성이 보장된 7단계 레이어의 상태 획득 (단방향 흐름 반영)
            packet = pipeline.get_system_snapshot()
            
            await websocket.send_text(json.dumps(packet))
            await asyncio.sleep(0.016) # ~60fps
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"WS Error: {e}")

# API 엔드포인트: 통합 명령 및 설정 (Unified Interface)
@app.post("/api/request")
async def handle_request(dto: UserRequestDTO, background_tasks: BackgroundTasks):
    """
    UI로부터의 모든 요청(명령, 설정 변경, 긴급정지)을 통합 처리합니다.
    Strict Interface 원칙에 따라 UserRequestDTO 규격을 강제합니다.
    """
    
    # 1. 텍스트 명령 처리
    if dto.request_type == UserRequestType.COMMAND:
        if dto.command:
            # [Fast Path] 긴급 정지 키워드 감지 시 에이전트 우회하여 즉시 정지
            cmd_lower = dto.command.lower()
            stop_keywords = ["멈춰", "정지", "stop", "관둬", "취소", "중단"]
            if any(k in cmd_lower for k in stop_keywords):
                from embodiment.robot_controller import robot_controller
                from strategy.visual_servoing import visual_servoing
                from shared.state_broadcaster import broadcaster
                
                broadcaster.publish("agent_thought", "🚨 긴급 정지 키워드 감지! 즉시 중단합니다.")
                
                # [Brain 중지]
                logic_brain.stop_agent()
                
                # [Action 중지]
                visual_servoing.stop()
                robot_controller.robot_driver.emergency_stop()
                return {"status": "stopped", "message": "Immediate stop executed"}

            background_tasks.add_task(logic_brain.execute_task, dto.command)
            return {"status": "accepted", "type": "command", "payload": dto.command}
    
    # 2. 시스템 설정 변경 처리
    elif dto.request_type == UserRequestType.CONFIG_CHANGE:
        if dto.config:
            # [Layer 1] 카메라 소스 변경
            perception_manager.bridge.switch_source(dto.config.active_camera)
            
            # [Layer 6] 로봇 대상 변경
            from embodiment.robot_controller import robot_controller
            robot_controller.switch_robot(dto.config.target_robot)
            
            # [Layer 4] 사고 방식(Logic Mode) 변경 반영
            strategy_manager.set_mode(dto.config.op_mode) 
            
            return {"status": "config_updated", "config": dto.config.dict()}
            
    # 3. 긴급 정지 처리
    elif dto.request_type == UserRequestType.EMERGENCY:
        from embodiment.robot_controller import robot_controller
        from strategy.visual_servoing import visual_servoing
        
        # [Brain 중지]
        logic_brain.stop_agent()
        
        # 1. 서보잉 루프 중단 (논리적 정지)
        visual_servoing.stop()
        
        # 2. 하드웨어 정지 (물리적 정지)
        robot_controller.robot_driver.emergency_stop()
        
        broadcaster.publish("agent_thought", "[System] UI를 통한 긴급 정지가 발동되었습니다.")
        return {"status": "emergency_stop_triggered"}

# 레거시 지원을 위한 기존 엔드포인트 유지 (내부적으로 handle_request 호출로 전환 가능)
@app.post("/api/command")
async def post_command(command: str, background_tasks: BackgroundTasks):
    # 하위 호환성을 위해 유지
    background_tasks.add_task(logic_brain.execute_task, command)
    return {"status": "accepted", "command": command}

@app.post("/api/config")
async def update_config(camera_source: str = None, robot_target: str = None, logic_mode: str = None):
    # 하위 호환성을 위해 유지 (DEPRECATED: /api/request 사용 권장)
    if camera_source:
        # [Fix] VisionBridge를 통해 소스 전환
        perception_manager.bridge.switch_source(camera_source)
    return {"status": "config_updated"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
