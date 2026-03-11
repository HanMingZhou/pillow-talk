"""OpenAI TTS adapter

Adapter for OpenAI Text-to-Speech API.
"""
import time
from typing import List, Dict, Any, Optional, Iterator
import structlog
from openai import AsyncOpenAI
from openai import OpenAIError, APITimeoutError, APIConnectionError

from .base import TTSAdapter
from ..models import AudioResult, VoiceProfile
from ...utils.exceptions import (
    TTSGenerationError,
    TTSProviderUnavailableError,
    ConfigurationError
)


logger = structlog.get_logger(__name__)


class OpenAIAdapter(TTSAdapter):
    """OpenAI TTS adapter
    
    Implements TTS using OpenAI's text-to-speech API.
    Supports multiple voices and streaming mode.
    """
    
    # Available voices from OpenAI
    SUPPORTED_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(
        self,
        api_key: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0
    ):
        """Initialize OpenAI adapter
        
        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_base: Exponential backoff base
        """
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.default_voice = "alloy"
        
        logger.info("OpenAI TTS adapter initialized")
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> AudioResult:
        """Generate audio from text using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice ID (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speech speed (0.25-4.0)
            audio_format: Audio format (mp3, opus, aac, flac)
            
        Returns:
            AudioResult with generated audio
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If OpenAI API is unreachable
        """
        voice = voice or self.default_voice
        
        # Validate voice
        if voice not in self.SUPPORTED_VOICES:
            logger.warning(
                "Invalid voice, using default",
                requested_voice=voice,
                default_voice=self.default_voice
            )
            voice = self.default_voice
        
        # Map format (OpenAI supports mp3, opus, aac, flac)
        openai_format = self._map_format(audio_format)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Generating audio with OpenAI",
                    attempt=attempt + 1,
                    voice=voice,
                    speed=speed,
                    format=openai_format,
                    text_length=len(text)
                )
                
                response = await self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text,
                    speed=speed,
                    response_format=openai_format
                )
                
                audio_data = response.content
                duration = self._estimate_duration(text, speed)
                
                logger.info(
                    "Audio generated successfully",
                    voice=voice,
                    duration=duration,
                    size_bytes=len(audio_data)
                )
                
                return AudioResult(
                    audio_data=audio_data,
                    format=audio_format,
                    duration=duration,
                    sample_rate=24000,  # OpenAI uses 24kHz
                    metadata={
                        'model': 'tts-1',
                        'voice': voice,
                        'speed': speed,
                        'provider': 'openai'
                    }
                )
            
            except APITimeoutError as e:
                last_error = e
                logger.warning(
                    "OpenAI API timeout, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except APIConnectionError as e:
                last_error = e
                logger.warning(
                    "OpenAI API connection error, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except OpenAIError as e:
                # Don't retry on other OpenAI errors (e.g., invalid request)
                logger.error(
                    "OpenAI API error",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise TTSGenerationError(f"OpenAI TTS generation failed: {e}")
            
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
            f"OpenAI TTS service unavailable after {self.max_retries} attempts: {last_error}"
        )
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> Iterator[bytes]:
        """Generate audio in streaming mode
        
        OpenAI supports streaming for TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice ID
            speed: Speech speed
            audio_format: Audio format
            
        Yields:
            Audio data chunks
        """
        voice = voice or self.default_voice
        openai_format = self._map_format(audio_format)
        
        try:
            logger.debug(
                "Starting streaming audio generation",
                voice=voice,
                speed=speed,
                format=openai_format
            )
            
            async with self.client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                input=text,
                speed=speed,
                response_format=openai_format
            ) as response:
                async for chunk in response.iter_bytes(chunk_size=4096):
                    yield chunk
            
            logger.info("Streaming audio generation completed")
        
        except Exception as e:
            logger.error(
                "Streaming audio generation failed",
                error=str(e)
            )
            raise TTSGenerationError(f"Streaming TTS generation failed: {e}")
    
    def get_voices(self) -> List[VoiceProfile]:
        """Get available OpenAI voices
        
        Returns:
            List of voice profiles
        """
        voices = [
            VoiceProfile(
                voice_id="alloy",
                name="Alloy",
                language="en-US",
                gender=None,
                provider_specific={'description': 'Neutral voice'}
            ),
            VoiceProfile(
                voice_id="echo",
                name="Echo",
                language="en-US",
                gender="male",
                provider_specific={'description': 'Male voice'}
            ),
            VoiceProfile(
                voice_id="fable",
                name="Fable",
                language="en-US",
                gender="male",
                provider_specific={'description': 'Male voice'}
            ),
            VoiceProfile(
                voice_id="onyx",
                name="Onyx",
                language="en-US",
                gender="male",
                provider_specific={'description': 'Male voice'}
            ),
            VoiceProfile(
                voice_id="nova",
                name="Nova",
                language="en-US",
                gender="female",
                provider_specific={'description': 'Female voice'}
            ),
            VoiceProfile(
                voice_id="shimmer",
                name="Shimmer",
                language="en-US",
                gender="female",
                provider_specific={'description': 'Female voice'}
            ),
        ]
        return voices
    
    def validate_config(self) -> bool:
        """Validate OpenAI adapter configuration
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.client.api_key:
            raise ConfigurationError("OpenAI API key is required")
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI API health
        
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            # Try a minimal API call to check connectivity
            # Use a very short text to minimize cost
            await self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input="test",
                response_format="mp3"
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'provider': 'openai',
                'details': {
                    'model': 'tts-1',
                    'voices_available': len(self.SUPPORTED_VOICES)
                }
            }
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'provider': 'openai',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    async def close(self) -> None:
        """Close OpenAI client"""
        await self.client.close()
        logger.info("OpenAI TTS adapter closed")
    
    def _map_format(self, format: str) -> str:
        """Map generic format to OpenAI format
        
        Args:
            format: Generic format (mp3, wav, ogg)
            
        Returns:
            OpenAI format (mp3, opus, aac, flac)
        """
        format_map = {
            'mp3': 'mp3',
            'wav': 'wav',  # OpenAI doesn't support wav, use flac
            'ogg': 'opus'  # Use opus for ogg
        }
        return format_map.get(format, 'mp3')
    
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
