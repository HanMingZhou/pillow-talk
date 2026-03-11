"""TTS data models

Data structures for TTS system components.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class AudioResult:
    """Result from TTS generation
    
    Represents the output of a text-to-speech conversion,
    including the audio data and metadata.
    """
    audio_data: bytes
    format: str  # 'mp3', 'wav', 'ogg'
    duration: float  # seconds
    sample_rate: int
    metadata: Dict[str, Any]


@dataclass
class VoiceProfile:
    """Voice configuration
    
    Describes an available voice for TTS generation.
    """
    voice_id: str
    name: str
    language: str
    gender: Optional[str] = None
    provider_specific: Optional[Dict[str, Any]] = None


@dataclass
class AudioResponse:
    """Audio generation response
    
    Response returned to API clients after audio generation.
    """
    audio_url: str
    duration: float
    format: str
    voice: str
    speed: float
