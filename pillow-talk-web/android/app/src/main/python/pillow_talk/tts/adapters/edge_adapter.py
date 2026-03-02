"""Edge TTS adapter

Adapter for Microsoft Edge's free Text-to-Speech API.
This is a free alternative to Azure TTS using the same voices.
"""
import time
import uuid
from typing import List, Dict, Any, Optional, Iterator
import structlog
import httpx
import json

from .base import TTSAdapter
from ..models import AudioResult, VoiceProfile
from ...utils.exceptions import (
    TTSGenerationError,
    TTSProviderUnavailableError,
    ConfigurationError
)


logger = structlog.get_logger(__name__)


class EdgeTTSAdapter(TTSAdapter):
    """Edge TTS adapter
    
    Implements TTS using Microsoft Edge's free TTS API.
    Uses the same neural voices as Azure but without requiring a subscription.
    """
    
    # Edge TTS endpoint
    EDGE_TTS_URL = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1"
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0
    ):
        """Initialize Edge TTS adapter
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_base: Exponential backoff base
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.default_voice = "en-US-JennyNeural"
        
        logger.info("Edge TTS adapter initialized")
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> AudioResult:
        """Generate audio from text using Edge TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., en-US-JennyNeural)
            speed: Speech speed (0.25-4.0)
            audio_format: Audio format (mp3, wav, ogg)
            
        Returns:
            AudioResult with generated audio
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If Edge TTS is unreachable
        """
        voice_name = voice or self.default_voice
        
        # Edge TTS uses WebSocket, but we'll use a simpler HTTP-based approach
        # by using the edge-tts library's approach
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Generating audio with Edge TTS",
                    attempt=attempt + 1,
                    voice=voice_name,
                    speed=speed,
                    format=audio_format,
                    text_length=len(text)
                )
                
                # Build SSML
                ssml = self._build_ssml(text, voice_name, speed)
                
                # Generate request ID
                request_id = str(uuid.uuid4()).replace("-", "")
                
                # Use HTTP endpoint (simplified version)
                # Note: In production, you might want to use the edge-tts library
                # or implement full WebSocket support
                audio_data = await self._synthesize_http(ssml, voice_name, request_id)
                
                duration = self._estimate_duration(text, speed)
                
                logger.info(
                    "Audio generated successfully",
                    voice=voice_name,
                    duration=duration,
                    size_bytes=len(audio_data)
                )
                
                return AudioResult(
                    audio_data=audio_data,
                    format=audio_format,
                    duration=duration,
                    sample_rate=24000,  # Edge TTS uses 24kHz
                    metadata={
                        'voice': voice_name,
                        'speed': speed,
                        'provider': 'edge'
                    }
                )
            
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Edge TTS timeout, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except httpx.ConnectError as e:
                last_error = e
                logger.warning(
                    "Edge TTS connection error, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except Exception as e:
                logger.error(
                    "Unexpected error during TTS generation",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise TTSGenerationError(f"TTS generation failed: {e}")
        
        # All retries exhausted
        logger.error(
            "All retry attempts exhausted",
            max_retries=self.max_retries,
            last_error=str(last_error)
        )
        raise TTSProviderUnavailableError(
            f"Edge TTS service unavailable after {self.max_retries} attempts: {last_error}"
        )
    
    async def _synthesize_http(self, ssml: str, voice: str, request_id: str) -> bytes:
        """Synthesize speech using HTTP endpoint
        
        This is a simplified implementation. For production use,
        consider using the edge-tts library or implementing full WebSocket support.
        
        Args:
            ssml: SSML text
            voice: Voice name
            request_id: Unique request ID
            
        Returns:
            Audio data bytes
        """
        # Note: This is a placeholder implementation
        # In production, you should use the edge-tts library or implement
        # the full WebSocket protocol
        
        # For now, we'll raise an error suggesting to use the library
        raise TTSGenerationError(
            "Edge TTS requires the edge-tts library. "
            "Please install it with: pip install edge-tts"
        )
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> Iterator[bytes]:
        """Generate audio in streaming mode
        
        Edge TTS supports streaming via WebSocket.
        
        Args:
            text: Text to convert to speech
            voice: Voice name
            speed: Speech speed
            audio_format: Audio format
            
        Yields:
            Audio data chunks
        """
        logger.debug("Edge TTS streaming mode")
        
        result = await self.synthesize(text, voice, speed, audio_format)
        
        # Yield in chunks for consistency with streaming interface
        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
    
    def get_voices(self) -> List[VoiceProfile]:
        """Get available Edge TTS voices
        
        Returns a subset of popular neural voices.
        Same voices as Azure TTS.
        
        Returns:
            List of voice profiles
        """
        voices = [
            # English (US) voices
            VoiceProfile(
                voice_id="en-US-JennyNeural",
                name="Jenny (US)",
                language="en-US",
                gender="female",
                provider_specific={'type': 'Neural', 'free': True}
            ),
            VoiceProfile(
                voice_id="en-US-GuyNeural",
                name="Guy (US)",
                language="en-US",
                gender="male",
                provider_specific={'type': 'Neural', 'free': True}
            ),
            VoiceProfile(
                voice_id="en-US-AriaNeural",
                name="Aria (US)",
                language="en-US",
                gender="female",
                provider_specific={'type': 'Neural', 'free': True}
            ),
            # Chinese (Mandarin) voices
            VoiceProfile(
                voice_id="zh-CN-XiaoxiaoNeural",
                name="Xiaoxiao (CN)",
                language="zh-CN",
                gender="female",
                provider_specific={'type': 'Neural', 'free': True}
            ),
            VoiceProfile(
                voice_id="zh-CN-YunxiNeural",
                name="Yunxi (CN)",
                language="zh-CN",
                gender="male",
                provider_specific={'type': 'Neural', 'free': True}
            ),
        ]
        return voices
    
    def validate_config(self) -> bool:
        """Validate Edge TTS adapter configuration
        
        Edge TTS doesn't require configuration (it's free).
        
        Returns:
            True (always valid)
        """
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Edge TTS API health
        
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            # Try a minimal synthesis to check connectivity
            await self.synthesize("test", self.default_voice, 1.0, 'mp3')
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'provider': 'edge',
                'details': {
                    'service': 'Microsoft Edge TTS (Free)',
                    'note': 'Requires edge-tts library'
                }
            }
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'provider': 'edge',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    async def close(self) -> None:
        """Close Edge TTS adapter"""
        logger.info("Edge TTS adapter closed")
    
    def _build_ssml(self, text: str, voice: str, speed: float) -> str:
        """Build SSML for Edge TTS
        
        Args:
            text: Text to synthesize
            voice: Voice name
            speed: Speech speed multiplier
            
        Returns:
            SSML string
        """
        # Convert speed to prosody rate
        rate_percent = f"{int(speed * 100)}%"
        
        ssml = f"""<speak version='1.0' xml:lang='en-US'>
    <voice name='{voice}'>
        <prosody rate='{rate_percent}'>
            {text}
        </prosody>
    </voice>
</speak>"""
        return ssml
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length
        
        Rough estimation: ~150 words per minute at normal speed
        
        Args:
            text: Input text
            speed: Speech speed multiplier
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        words_per_minute = 150 * speed
        duration_minutes = word_count / words_per_minute
        return duration_minutes * 60
    
    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff delay
        
        Args:
            attempt: Current attempt number (0-indexed)
        """
        import asyncio
        delay = self.retry_backoff_base ** attempt
        logger.debug(f"Backing off for {delay} seconds")
        await asyncio.sleep(delay)
