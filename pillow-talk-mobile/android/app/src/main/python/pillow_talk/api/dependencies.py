"""API 依赖注入

提供 FastAPI 依赖注入函数，用于管理服务实例和请求上下文。
"""
import uuid
from functools import lru_cache
from typing import Generator
import structlog

from ..config import settings
from ..core.conversation import ConversationManager
from ..core.image import ImagePreprocessor
from ..core.prompt import PromptEngine
from ..tts import TTSSystem, ConfigurationManager as TTSConfigManager


logger = structlog.get_logger(__name__)


# 全局单例实例
_conversation_manager: ConversationManager | None = None
_image_preprocessor: ImagePreprocessor | None = None
_prompt_engine: PromptEngine | None = None
_tts_system: TTSSystem | None = None


@lru_cache()
def get_settings():
    """获取应用配置
    
    Returns:
        Settings: 应用配置实例
    """
    return settings


def get_logger() -> structlog.BoundLogger:
    """获取日志记录器
    
    Returns:
        structlog.BoundLogger: 日志记录器实例
    """
    return logger


def get_conversation_manager() -> ConversationManager:
    """获取对话管理器单例
    
    Returns:
        ConversationManager: 对话管理器实例
    """
    global _conversation_manager
    
    if _conversation_manager is None:
        _conversation_manager = ConversationManager(
            cache_ttl=settings.conversation_ttl,
            max_history=settings.max_conversation_history
        )
        logger.info("Conversation manager initialized")
    
    return _conversation_manager


def get_image_preprocessor() -> ImagePreprocessor:
    """获取图像预处理器单例
    
    Returns:
        ImagePreprocessor: 图像预处理器实例
    """
    global _image_preprocessor
    
    if _image_preprocessor is None:
        _image_preprocessor = ImagePreprocessor(
            max_size_mb=settings.max_image_size_mb,
            quality=settings.image_quality
        )
        logger.info("Image preprocessor initialized")
    
    return _image_preprocessor


def get_prompt_engine() -> PromptEngine:
    """获取 Prompt 引擎单例
    
    Returns:
        PromptEngine: Prompt 引擎实例
    """
    global _prompt_engine
    
    if _prompt_engine is None:
        _prompt_engine = PromptEngine()
        logger.info("Prompt engine initialized")
    
    return _prompt_engine


def get_tts_system() -> TTSSystem | None:
    """获取 TTS 系统单例
    
    Returns:
        TTSSystem | None: TTS 系统实例，如果未配置则返回 None
    """
    global _tts_system
    
    if _tts_system is None:
        # 尝试加载 TTS 配置
        tts_config_path = getattr(settings, 'tts_config_path', None)
        
        if tts_config_path:
            try:
                tts_config_manager = TTSConfigManager(config_path=tts_config_path)
                _tts_system = TTSSystem(tts_config_manager.config)
                logger.info("TTS system initialized")
            except Exception as e:
                logger.warning(
                    "Failed to initialize TTS system, TTS will be disabled",
                    error=str(e)
                )
                return None
        else:
            logger.info("TTS config path not set, TTS disabled")
            return None
    
    return _tts_system


def get_request_id() -> str:
    """生成唯一的请求 ID
    
    Returns:
        str: UUID 格式的请求 ID
    """
    return str(uuid.uuid4())


async def cleanup_resources() -> None:
    """清理全局资源
    
    在应用关闭时调用，清理所有单例实例。
    """
    global _conversation_manager, _image_preprocessor, _prompt_engine, _tts_system
    
    logger.info("Cleaning up resources")
    
    # 清理 TTS 系统
    if _tts_system:
        await _tts_system.close()
        _tts_system = None
    
    # 清理对话管理器
    if _conversation_manager:
        _conversation_manager.cleanup_expired()
        _conversation_manager = None
    
    # 重置其他单例
    _image_preprocessor = None
    _prompt_engine = None
    
    logger.info("Resources cleaned up")
