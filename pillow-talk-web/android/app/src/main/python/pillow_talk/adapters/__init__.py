"""模型适配器模块

提供统一的模型适配器工厂
"""
from typing import Dict, Type, Any
from .base import MultimodalInterface
from .openai import OpenAIAdapter
from .doubao import DoubaoAdapter
from .qwen import QwenAdapter
from .glm import GLMAdapter
from .gemini import GeminiAdapter
from .claude import ClaudeAdapter
from .custom import CustomAdapter
from ..utils.exceptions import ConfigurationError


class ModelAdapterFactory:
    """模型适配器工厂
    
    根据提供商创建对应的模型适配器实例
    """
    
    # 注册的适配器类
    _adapters: Dict[str, Type[MultimodalInterface]] = {
        "openai": OpenAIAdapter,
        "doubao": DoubaoAdapter,
        "qwen": QwenAdapter,
        "glm": GLMAdapter,
        "gemini": GeminiAdapter,
        "claude": ClaudeAdapter,
        "custom": CustomAdapter,
    }
    
    @classmethod
    def create_adapter(
        cls,
        provider: str,
        **config: Any
    ) -> MultimodalInterface:
        """创建模型适配器
        
        Args:
            provider: 提供商名称（openai/doubao/qwen/gemini/claude/custom）
            **config: 适配器配置参数
            
        Returns:
            模型适配器实例
            
        Raises:
            ConfigurationError: 不支持的提供商或配置错误
        """
        adapter_class = cls._adapters.get(provider)
        
        if not adapter_class:
            raise ConfigurationError(
                f"Unsupported provider: {provider}. "
                f"Supported providers: {', '.join(cls._adapters.keys())}"
            )
        
        try:
            return adapter_class(**config)
        except TypeError as e:
            raise ConfigurationError(
                f"Invalid configuration for {provider} adapter: {str(e)}"
            )
    
    @classmethod
    def register_adapter(
        cls,
        provider: str,
        adapter_class: Type[MultimodalInterface]
    ) -> None:
        """注册新的适配器
        
        Args:
            provider: 提供商名称
            adapter_class: 适配器类
        """
        cls._adapters[provider] = adapter_class
    
    @classmethod
    def list_providers(cls) -> list[str]:
        """列出所有支持的提供商
        
        Returns:
            提供商名称列表
        """
        return list(cls._adapters.keys())


__all__ = [
    "MultimodalInterface",
    "OpenAIAdapter",
    "DoubaoAdapter",
    "QwenAdapter",
    "GLMAdapter",
    "GeminiAdapter",
    "ClaudeAdapter",
    "CustomAdapter",
    "ModelAdapterFactory",
]
