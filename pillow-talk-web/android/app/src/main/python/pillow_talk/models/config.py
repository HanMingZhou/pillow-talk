"""内部配置和数据模型

定义系统内部使用的数据结构
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class Message(BaseModel):
    """对话消息"""
    role: str = Field(..., description="角色（user/assistant/system）")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="消息时间戳"
    )


class Conversation(BaseModel):
    """对话会话"""
    conversation_id: str = Field(..., description="对话 ID")
    messages: List[Message] = Field(default_factory=list, description="消息列表")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now,
        description="最后活动时间"
    )
    max_history: int = Field(default=10, description="最大历史记录数")


class RequestMetrics(BaseModel):
    """请求指标"""
    request_id: str = Field(..., description="请求 ID")
    endpoint: str = Field(..., description="API 端点")
    method: str = Field(..., description="HTTP 方法")
    status_code: int = Field(..., description="HTTP 状态码")
    latency_ms: int = Field(..., description="总延迟（毫秒）")
    image_processing_ms: int = Field(
        default=0,
        description="图像处理耗时（毫秒）"
    )
    model_call_ms: int = Field(default=0, description="模型调用耗时（毫秒）")
    tts_generation_ms: int = Field(
        default=0,
        description="TTS 生成耗时（毫秒）"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="时间戳"
    )
