"""TTS configuration models

Configuration management for the flexible TTS system.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TTSMode(str, Enum):
    """TTS operational mode"""
    LOCAL = "local"
    CLOUD = "cloud"
    SELF_HOSTED = "self-hosted"


class CloudProvider(str, Enum):
    """Cloud TTS provider"""
    OPENAI = "openai"
    GOOGLE = "google"


class SelfHostedProvider(str, Enum):
    """Self-hosted TTS provider"""
    VITS = "vits"
    BARK = "bark"
    XTTS = "xtts"
    COQUI = "coqui"


class TTSConfig(BaseModel):
    """TTS system configuration
    
    Validates configuration at initialization and ensures
    mode-specific requirements are met.
    """
    
    # Mode configuration
    mode: TTSMode = Field(..., description="TTS operational mode")
    cloud_provider: Optional[CloudProvider] = Field(
        default=None,
        description="Cloud provider (required when mode is 'cloud')"
    )
    self_hosted_provider: Optional[SelfHostedProvider] = Field(
        default=None,
        description="Self-hosted provider (required when mode is 'self-hosted')"
    )
    
    # API credentials
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    google_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to Google Cloud credentials JSON"
    )
    
    # Self-hosted endpoints
    self_hosted_endpoint: Optional[str] = Field(
        default=None,
        description="Self-hosted TTS service endpoint URL"
    )
    
    # Audio settings
    default_voice: str = Field(
        default="default",
        description="Default voice to use"
    )
    default_speed: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Default speech speed (0.25-4.0)"
    )
    default_format: str = Field(
        default="mp3",
        description="Default audio format (mp3, wav, ogg)"
    )
    max_text_length: int = Field(
        default=5000,
        ge=1,
        description="Maximum text length for TTS"
    )
    
    # Storage settings
    storage_type: str = Field(
        default="local",
        description="Storage type: 'local' or 'cloud'"
    )
    local_storage_path: str = Field(
        default="./audio_files",
        description="Local storage directory path"
    )
    cloud_storage_bucket: Optional[str] = Field(
        default=None,
        description="Cloud storage bucket name"
    )
    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for audio file access"
    )
    
    # Cleanup settings
    audio_expiration_hours: int = Field(
        default=24,
        ge=1,
        description="Audio file expiration time in hours"
    )
    cleanup_interval_hours: int = Field(
        default=1,
        ge=1,
        description="Cleanup service run interval in hours"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum requests per minute per IP"
    )
    
    # Text preprocessing
    url_handling: str = Field(
        default="replace",
        description="URL handling: 'replace', 'remove', or 'keep'"
    )
    code_block_handling: str = Field(
        default="replace",
        description="Code block handling: 'replace', 'skip', or 'keep'"
    )
    strip_markdown: bool = Field(
        default=True,
        description="Whether to strip markdown formatting"
    )
    
    # Retry settings
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum retry attempts for cloud providers"
    )
    retry_backoff_base: float = Field(
        default=2.0,
        ge=1.0,
        description="Exponential backoff base for retries"
    )
    
    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v: TTSMode) -> TTSMode:
        """Validate TTS mode is valid"""
        if v not in TTSMode:
            raise ValueError(
                f"Invalid TTS mode: {v}. "
                f"Must be one of: {', '.join([m.value for m in TTSMode])}"
            )
        return v
    
    @field_validator('cloud_provider')
    @classmethod
    def validate_cloud_provider(cls, v: Optional[CloudProvider], info) -> Optional[CloudProvider]:
        """Validate cloud provider is specified when mode is cloud"""
        mode = info.data.get('mode')
        if mode == TTSMode.CLOUD and v is None:
            raise ValueError(
                "cloud_provider is required when mode is 'cloud'. "
                f"Must be one of: {', '.join([p.value for p in CloudProvider])}"
            )
        return v
    
    @field_validator('self_hosted_provider')
    @classmethod
    def validate_self_hosted_provider(
        cls,
        v: Optional[SelfHostedProvider],
        info
    ) -> Optional[SelfHostedProvider]:
        """Validate self-hosted provider is specified when mode is self-hosted"""
        mode = info.data.get('mode')
        if mode == TTSMode.SELF_HOSTED and v is None:
            raise ValueError(
                "self_hosted_provider is required when mode is 'self-hosted'. "
                f"Must be one of: {', '.join([p.value for p in SelfHostedProvider])}"
            )
        return v
    
    @field_validator('default_format')
    @classmethod
    def validate_audio_format(cls, v: str) -> str:
        """Validate audio format is supported"""
        supported_formats = ['mp3', 'wav', 'ogg']
        if v not in supported_formats:
            raise ValueError(
                f"Invalid audio format: {v}. "
                f"Must be one of: {', '.join(supported_formats)}"
            )
        return v
    
    @field_validator('storage_type')
    @classmethod
    def validate_storage_type(cls, v: str) -> str:
        """Validate storage type is supported"""
        supported_types = ['local', 'cloud']
        if v not in supported_types:
            raise ValueError(
                f"Invalid storage type: {v}. "
                f"Must be one of: {', '.join(supported_types)}"
            )
        return v
    
    @field_validator('url_handling')
    @classmethod
    def validate_url_handling(cls, v: str) -> str:
        """Validate URL handling strategy"""
        valid_strategies = ['replace', 'remove', 'keep']
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid URL handling: {v}. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )
        return v
    
    @field_validator('code_block_handling')
    @classmethod
    def validate_code_block_handling(cls, v: str) -> str:
        """Validate code block handling strategy"""
        valid_strategies = ['replace', 'skip', 'keep']
        if v not in valid_strategies:
            raise ValueError(
                f"Invalid code block handling: {v}. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )
        return v
