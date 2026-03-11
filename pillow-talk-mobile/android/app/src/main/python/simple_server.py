"""
简化的 Android Python Backend Server
直接使用 HTTP 请求调用豆包 API，避免复杂依赖
"""
import os
import base64
import json
import uuid
from io import BytesIO
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import requests

app = FastAPI(title="Pillow Talk API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 豆包配置
DOUBAO_API_KEY = "38966765-e8a8-4a3f-b311-362f1cb23c52"
DOUBAO_MODEL = "doubao-seed-1-6-flash-250828"
DOUBAO_API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

class ChatResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: dict
    request_id: str

@app.get("/")
async def root():
    return {"message": "Pillow Talk API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    image: UploadFile = File(...),
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None)
):
    """处理聊天请求"""
    try:
        # 读取并处理图片
        image_data = await image.read()
        img = Image.open(BytesIO(image_data))
        
        # 转换为 base64
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # 构建豆包 API 请求
        headers = {
            "Authorization": f"Bearer {DOUBAO_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": DOUBAO_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个友好的助手，可以看到用户的摄像头画面。请用简短、自然的方式回应用户。"
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            ]
        }
        
        # 调用豆包 API
        response = requests.post(
            DOUBAO_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Doubao API error: {response.text}"
            )
        
        result = response.json()
        
        # 提取回复文本
        reply_text = result.get("choices", [{}])[0].get("message", {}).get("content", "抱歉，我无法回应。")
        
        return ChatResponse(
            code=0,
            message="success",
            data={
                "text": reply_text,
                "audio_url": None,
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "latency_ms": 0,
                "token_usage": None
            },
            request_id=str(uuid.uuid4())
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
