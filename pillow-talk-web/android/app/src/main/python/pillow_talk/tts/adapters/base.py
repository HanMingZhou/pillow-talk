"""Base TTS adapter interface

Abstract base class for all TTS provider adapters.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator

from ..models import AudioResult, VoiceProfile


class TTSAdapter(ABC):
    """Base interface for all TTS providers
    
    All TTS adapters must implement this interface to ensure
    consistent behavior across different providers.
    """
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> AudioResult:
        """Generate audio from text
        
        Args:
            text: Text to convert to speech
            voice: Voice ID to use (None for default)
            speed: Speech speed multiplier (0.25-4.0)
            audio_format: Desired audio format ('mp3', 'wav', 'ogg')
            
        Returns:
            AudioResult with generated audio
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If provider is unreachable
        """
        pass
    
    @abstractmethod
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> Iterator[bytes]:
        """Generate audio from text in streaming mode
        
        Yields audio chunks as they are generated.
        Falls back to non-streaming if not supported.
        
        Args:
            text: Text to convert to speech
            voice: Voice ID to use (None for default)
            speed: Speech speed multiplier (0.25-4.0)
            audio_format: Desired audio format
            
        Yields:
            Audio data chunks
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If provider is unreachable
        """
        pass
    
    @abstractmethod
    def get_voices(self) -> List[VoiceProfile]:
        """Get available voices for this provider
        
        Returns:
            List of available voice profiles
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate adapter configuration
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health and connectivity
        
        Returns:
            Dict with status, response_time, and details
            Example: {
                'status': 'healthy',
                'response_time_ms': 150,
                'provider': 'openai',
                'details': {}
            }
        """
        pass
    
    async def close(self) -> None:
        """Close adapter and cleanup resources
        
        Optional method for cleanup. Override if needed.
        """
        pass
