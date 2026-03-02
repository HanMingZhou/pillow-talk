"""Google Cloud TTS adapter

Adapter for Google Cloud Text-to-Speech API.
"""
import time
from typing import List, Dict, Any, Optional, Iterator
import structlog
from google.cloud import texttospeech
from google.api_core import exceptions as google_exceptions

from .base import TTSAdapter
from ..models import AudioResult, VoiceProfile
from ...utils.exceptions import (
    TTSGenerationError,
    TTSProviderUnavailableError,
    ConfigurationError
)


logger = structlog.get_logger(__name__)


class GoogleTTSAdapter(TTSAdapter):
    """Google Cloud TTS adapter
    
    Implements TTS using Google Cloud Text-to-Speech API.
    Supports multiple languages and voices.
    """
    
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0
    ):
        """Initialize Google Cloud TTS adapter
        
        Args:
            credentials_path: Path to Google Cloud credentials JSON file
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_base: Exponential backoff base
        """
        if credentials_path:
            self.client = texttospeech.TextToSpeechClient.from_service_account_json(
                credentials_path
            )
        else:
            # Use default credentials from environment
            self.client = texttospeech.TextToSpeechClient()
        
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.default_voice = "en-US-Neural2-C"
        self.default_language = "en-US"
        
        logger.info("Google Cloud TTS adapter initialized")
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> AudioResult:
        """Generate audio from text using Google Cloud TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., en-US-Neural2-C)
            speed: Speech speed (0.25-4.0)
            audio_format: Audio format (mp3, wav, ogg)
            
        Returns:
            AudioResult with generated audio
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If Google Cloud API is unreachable
        """
        voice_name = voice or self.default_voice
        
        # Parse language code from voice name
        language_code = self._extract_language_code(voice_name)
        
        # Map format to Google Cloud encoding
        audio_encoding = self._map_format(audio_format)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Generating audio with Google Cloud TTS",
                    attempt=attempt + 1,
                    voice=voice_name,
                    speed=speed,
                    format=audio_encoding,
                    text_length=len(text)
                )
                
                # Set the text input
                synthesis_input = texttospeech.SynthesisInput(text=text)
                
                # Build the voice request
                voice_params = texttospeech.VoiceSelectionParams(
                    language_code=language_code,
                    name=voice_name
                )
                
                # Select the audio config
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=audio_encoding,
                    speaking_rate=speed
                )
                
                # Perform the text-to-speech request
                response = self.client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice_params,
                    audio_config=audio_config,
                    timeout=self.timeout
                )
                
                audio_data = response.audio_content
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
                    sample_rate=24000,  # Google Cloud uses 24kHz
                    metadata={
                        'voice': voice_name,
                        'language': language_code,
                        'speed': speed,
                        'provider': 'google'
                    }
                )
            
            except google_exceptions.DeadlineExceeded as e:
                last_error = e
                logger.warning(
                    "Google Cloud API timeout, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except google_exceptions.ServiceUnavailable as e:
                last_error = e
                logger.warning(
                    "Google Cloud API unavailable, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except google_exceptions.GoogleAPIError as e:
                # Don't retry on other Google API errors
                logger.error(
                    "Google Cloud API error",
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise TTSGenerationError(f"Google Cloud TTS generation failed: {e}")
            
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
            f"Google Cloud TTS service unavailable after {self.max_retries} attempts: {last_error}"
        )
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> Iterator[bytes]:
        """Generate audio in streaming mode
        
        Google Cloud TTS doesn't support true streaming,
        so we fall back to non-streaming and yield the complete audio.
        
        Args:
            text: Text to convert to speech
            voice: Voice name
            speed: Speech speed
            audio_format: Audio format
            
        Yields:
            Audio data chunks
        """
        logger.debug("Google Cloud TTS doesn't support streaming, using non-streaming mode")
        
        result = await self.synthesize(text, voice, speed, audio_format)
        
        # Yield in chunks for consistency with streaming interface
        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
    
    def get_voices(self) -> List[VoiceProfile]:
        """Get available Google Cloud voices
        
        Returns a subset of popular voices. For full list, use the API.
        
        Returns:
            List of voice profiles
        """
        voices = [
            # English (US) voices
            VoiceProfile(
                voice_id="en-US-Neural2-C",
                name="en-US-Neural2-C",
                language="en-US",
                gender="female",
                provider_specific={'type': 'Neural2'}
            ),
            VoiceProfile(
                voice_id="en-US-Neural2-D",
                name="en-US-Neural2-D",
                language="en-US",
                gender="male",
                provider_specific={'type': 'Neural2'}
            ),
            VoiceProfile(
                voice_id="en-US-Neural2-F",
                name="en-US-Neural2-F",
                language="en-US",
                gender="female",
                provider_specific={'type': 'Neural2'}
            ),
            # Chinese (Mandarin) voices
            VoiceProfile(
                voice_id="cmn-CN-Wavenet-A",
                name="cmn-CN-Wavenet-A",
                language="cmn-CN",
                gender="female",
                provider_specific={'type': 'Wavenet'}
            ),
            VoiceProfile(
                voice_id="cmn-CN-Wavenet-B",
                name="cmn-CN-Wavenet-B",
                language="cmn-CN",
                gender="male",
                provider_specific={'type': 'Wavenet'}
            ),
        ]
        return voices
    
    def validate_config(self) -> bool:
        """Validate Google Cloud TTS adapter configuration
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Try to list voices to validate credentials
            self.client.list_voices()
            return True
        except Exception as e:
            raise ConfigurationError(f"Google Cloud TTS configuration invalid: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Google Cloud TTS API health
        
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            # Try a minimal API call to check connectivity
            synthesis_input = texttospeech.SynthesisInput(text="test")
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-C"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
                timeout=10.0
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'provider': 'google',
                'details': {
                    'service': 'Google Cloud Text-to-Speech'
                }
            }
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'provider': 'google',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    async def close(self) -> None:
        """Close Google Cloud TTS client"""
        # Google Cloud client doesn't require explicit closing
        logger.info("Google Cloud TTS adapter closed")
    
    def _map_format(self, format: str) -> texttospeech.AudioEncoding:
        """Map generic format to Google Cloud encoding
        
        Args:
            format: Generic format (mp3, wav, ogg)
            
        Returns:
            Google Cloud AudioEncoding
        """
        format_map = {
            'mp3': texttospeech.AudioEncoding.MP3,
            'wav': texttospeech.AudioEncoding.LINEAR16,
            'ogg': texttospeech.AudioEncoding.OGG_OPUS
        }
        return format_map.get(format, texttospeech.AudioEncoding.MP3)
    
    def _extract_language_code(self, voice_name: str) -> str:
        """Extract language code from voice name
        
        Args:
            voice_name: Voice name (e.g., en-US-Neural2-C)
            
        Returns:
            Language code (e.g., en-US)
        """
        # Voice names typically start with language code
        parts = voice_name.split('-')
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return self.default_language
    
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
