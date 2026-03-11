"""应用配置管理模块

使用 pydantic-settings 从环境变量加载配置
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类
    
    所有配置项从环境变量或 .env 文件加载
    """
    
    # 应用配置
    app_name: str = Field(default="Pillow Talk Backend", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机地址")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    workers: int = Field(default=4, ge=1, description="工作进程数")
    
    # 安全配置
    encryption_key: str = Field(..., description="加密密钥（必需）")
    allowed_origins: List[str] = Field(
        default=["*"],
        description="允许的 CORS 来源"
    )
    
    # 限流配置
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="每分钟每 IP 最大请求数"
    )
    rate_limit_per_api_key: int = Field(
        default=100,
        ge=1,
        description="每分钟每 API Key 最大请求数"
    )
    
    # 对话配置
    conversation_ttl: int = Field(
        default=1800,
        ge=60,
        description="对话过期时间（秒）"
    )
    max_conversation_history: int = Field(
        default=10,
        ge=1,
        description="最大对话历史轮数"
    )
    
    # 图像处理配置
    max_image_size_mb: float = Field(
        default=1.0,
        gt=0,
        description="最大图像大小（MB）"
    )
    image_quality: int = Field(
        default=85,
        ge=1,
        le=100,
        description="JPEG 压缩质量"
    )
    
    # 模型配置
    model_timeout: int = Field(
        default=30,
        ge=1,
        description="模型调用超时时间（秒）"
    )
    model_max_retries: int = Field(
        default=3,
        ge=0,
        description="模型调用最大重试次数"
    )
    
    # TTS 配置
    tts_timeout: int = Field(
        default=10,
        ge=1,
        description="TTS 服务超时时间（秒）"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别（DEBUG/INFO/WARNING/ERROR）"
    )
    log_format: str = Field(
        default="json",
        description="日志格式（json/text）"
    )
    
    # 可选的 API Keys
    openai_api_key: str | None = Field(default=None, description="OpenAI API Key")
    openai_model: str | None = Field(default=None, description="OpenAI 模型名称")
    openai_base_url: str | None = Field(default=None, description="OpenAI Base URL")
    
    google_api_key: str | None = Field(default=None, description="Google API Key")
    gemini_model: str | None = Field(default=None, description="Gemini 模型名称")
    
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API Key")
    claude_model: str | None = Field(default=None, description="Claude 模型名称")
    
    doubao_api_key: str | None = Field(default=None, description="豆包 API Key")
    doubao_model: str | None = Field(default=None, description="豆包模型名称")
    doubao_base_url: str | None = Field(default=None, description="豆包 Base URL")
    
    glm_api_key: str | None = Field(default=None, description="智谱 GLM API Key")
    glm_model: str | None = Field(default=None, description="GLM 模型名称")
    
    gemini_api_key: str | None = Field(default=None, description="Gemini API Key")
    
    qwen_api_key: str | None = Field(default=None, description="千问 API Key")
    qwen_model: str | None = Field(default=None, description="千问模型名称")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def validate_required_fields(self) -> None:
        """验证必需字段是否已设置
        
        Raises:
            ValueError: 当必需字段缺失时
        """
        if not self.encryption_key or self.encryption_key == "your-secret-encryption-key-here-change-in-production":
            raise ValueError(
                "ENCRYPTION_KEY must be set to a secure value in production"
            )


# 全局配置实例
settings = Settings()
