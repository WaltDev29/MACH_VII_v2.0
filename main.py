import uvicorn
import os
import sys
import logging

from shared.config import PathConfig

# 로깅 설정 (프로그램 시작 시 가장 먼저)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

# 프로젝트 루트를 Python Path에 추가
BASE_DIR = PathConfig.BASE_DIR
sys.path.append(str(BASE_DIR))

from interface.backend.api_server import app

# 초기 실행 시 필수 디렉토리 확인 및 생성
PathConfig.ensure_dirs()

def main():
    print("==========================================")
    print("   MACH-VII v2.0 System Initializing...   ")
    print("==========================================")
    
    # 1. 초기화 (Initialization)
    # 실제 초기화 로직은 api_server.py의 @app.on_event("startup")에서 수행됨
    # 추후 여기서 명시적으로 순서를 제어할 수 있음
    
    # 2. 실행 (Execution)
    print("[Main] Starting Backend API Server...")
    # reload=True는 개발 모드에서 유용
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
