"""TTS (Text-to-Speech) module

Flexible TTS system supporting multiple providers:
- Local (client-side)
- Cloud (OpenAI, Google Cloud)
- Self-hosted (VITS, Bark, XTTS, Coqui)
"""
from .config import TTSConfig, TTSMode, CloudProvider, SelfHostedProvider
from .manager import ConfigurationManager
from .models import AudioResult, VoiceProfile, AudioResponse
from .system import TTSSystem
from .storage import AudioStorage
from .preprocessor import TextPreprocessor

__all__ = [
    'TTSConfig',
    'TTSMode',
    'CloudProvider',
    'SelfHostedProvider',
    'ConfigurationManager',
    'AudioResult',
    'VoiceProfile',
    'AudioResponse',
    'TTSSystem',
    'AudioStorage',
    'TextPreprocessor',
]
