"""
Android Python Backend Server
在 Android 上启动 FastAPI 后端服务
"""
import os
import sys
from pillow_talk.main import app

# 设置环境变量
os.environ.setdefault("DOUBAO_API_KEY", "38966765-e8a8-4a3f-b311-362f1cb23c52")
os.environ.setdefault("DOUBAO_MODEL", "doubao-seed-1-6-flash-250828")
os.environ.setdefault("ALLOWED_ORIGINS", '["*"]')
os.environ.setdefault("LOG_LEVEL", "INFO")

def start_server(port=8000):
    """启动 FastAPI 服务器"""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    start_server()
