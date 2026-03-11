"""响应数据模型

定义所有 API 响应的 Pydantic 模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatData(BaseModel):
    """对话数据"""
    text: str = Field(..., description="AI 生成的文本")
    audio_url: Optional[str] = Field(default=None, description="音频文件 URL")
    conversation_id: str = Field(..., description="对话 ID")
    latency_ms: int = Field(..., description="处理延迟（毫秒）")
    token_usage: Optional[Dict[str, int]] = Field(
        default=None,
        description="Token 使用量"
    )


class ChatResponse(BaseModel):
    """对话响应"""
    code: int = Field(..., description="状态码（0 表示成功）")
    message: str = Field(..., description="响应消息")
    data: Optional[ChatData] = Field(default=None, description="响应数据")
    request_id: str = Field(..., description="请求 ID")


class TestConnectionData(BaseModel):
    """测试连接数据"""
    success: bool = Field(..., description="连接是否成功")
    latency_ms: int = Field(..., description="连接延迟（毫秒）")
    error_message: Optional[str] = Field(
        default=None,
        description="错误消息（如果失败）"
    )


class TestConnectionResponse(BaseModel):
    """测试连接响应"""
    code: int = Field(..., description="状态码（0 表示成功）")
    message: str = Field(..., description="响应消息")
    data: TestConnectionData = Field(..., description="测试结果数据")
    request_id: str = Field(..., description="请求 ID")


class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型 ID")
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="提供商")
    supports_vision: bool = Field(..., description="是否支持视觉输入")
    supports_streaming: bool = Field(..., description="是否支持流式输出")
    description: str = Field(..., description="模型描述")


class ModelsResponse(BaseModel):
    """模型列表响应"""
    code: int = Field(..., description="状态码（0 表示成功）")
    message: str = Field(..., description="响应消息")
    data: List[ModelInfo] = Field(..., description="模型列表")


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    error_type: str = Field(..., description="错误类型")
    suggestion: str = Field(..., description="解决建议")
    request_id: str = Field(..., description="请求 ID")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="应用版本")
    timestamp: str = Field(..., description="时间戳")
