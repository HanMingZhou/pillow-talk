"""请求数据模型

定义所有 API 请求的 Pydantic 模型
"""
import base64
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ModelProvider(str, Enum):
    """模型提供商枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    DOUBAO = "doubao"
    QWEN = "qwen"
    GLM = "glm"
    CUSTOM = "custom"


class CustomModelConfig(BaseModel):
    """自定义模型配置"""
    base_url: str = Field(..., description="模型 API 基础 URL")
    api_key: str = Field(..., description="API 密钥")
    model_name: str = Field(..., description="模型名称")
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="自定义 HTTP 头"
    )
    
    @field_validator("base_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证 URL 格式"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip("/")


class ChatRequest(BaseModel):
    """对话请求模型"""
    image_base64: str = Field(..., description="Base64 编码的图像数据")
    system_prompt: str = Field(
        ...,
        max_length=2000,
        description="系统提示词"
    )
    provider: ModelProvider = Field(..., description="模型提供商")
    custom_config: Optional[CustomModelConfig] = Field(
        default=None,
        description="自定义模型配置（provider 为 custom 时必填）"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="对话 ID（用于多轮对话）"
    )
    stream: bool = Field(default=False, description="是否使用流式输出")
    tts_enabled: bool = Field(default=True, description="是否启用 TTS")
    tts_voice: str = Field(default="default", description="语音类型")
    tts_speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="语速（0.5-2.0）"
    )
    
    @field_validator("image_base64")
    @classmethod
    def validate_image(cls, v: str) -> str:
        """验证 Base64 编码的图像数据"""
        if not v:
            raise ValueError("image_base64 cannot be empty")
        
        # 移除可能的 data URL 前缀
        if v.startswith("data:image"):
            v = v.split(",", 1)[1] if "," in v else v
        
        # 验证 Base64 格式
        try:
            base64.b64decode(v)
        except Exception as e:
            raise ValueError(f"Invalid Base64 encoding: {e}")
        
        return v
    
    @field_validator("custom_config")
    @classmethod
    def validate_custom_config(cls, v: Optional[CustomModelConfig], info: Any) -> Optional[CustomModelConfig]:
        """验证自定义配置"""
        provider = info.data.get("provider")
        if provider == ModelProvider.CUSTOM and v is None:
            raise ValueError("custom_config is required when provider is 'custom'")
        return v


class TestConnectionRequest(BaseModel):
    """测试连接请求模型"""
    provider: ModelProvider = Field(..., description="模型提供商")
    custom_config: Optional[CustomModelConfig] = Field(
        default=None,
        description="自定义模型配置"
    )
    
    @field_validator("custom_config")
    @classmethod
    def validate_custom_config(cls, v: Optional[CustomModelConfig], info: Any) -> Optional[CustomModelConfig]:
        """验证自定义配置"""
        provider = info.data.get("provider")
        if provider == ModelProvider.CUSTOM and v is None:
            raise ValueError("custom_config is required when provider is 'custom'")
        return v
