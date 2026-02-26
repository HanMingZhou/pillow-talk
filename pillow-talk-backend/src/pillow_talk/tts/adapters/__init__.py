"""TTS adapters

Adapter implementations for different TTS providers.
"""
from .base import TTSAdapter
from .openai_adapter import OpenAIAdapter

__all__ = ['TTSAdapter', 'OpenAIAdapter']
