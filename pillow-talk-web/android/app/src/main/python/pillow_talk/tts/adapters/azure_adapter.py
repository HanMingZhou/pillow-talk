"""Azure TTS adapter

Adapter for Microsoft Azure Cognitive Services Text-to-Speech API.
"""
import time
from typing import List, Dict, Any, Optional, Iterator
import structlog
import httpx

from .base import TTSAdapter
from ..models import AudioResult, VoiceProfile
from ...utils.exceptions import (
    TTSGenerationError,
    TTSProviderUnavailableError,
    ConfigurationError
)


logger = structlog.get_logger(__name__)


class AzureTTSAdapter(TTSAdapter):
    """Azure Cognitive Services TTS adapter
    
    Implements TTS using Microsoft Azure Cognitive Services Speech API.
    Supports multiple languages and neural voices.
    """
    
    def __init__(
        self,
        subscription_key: str,
        region: str = "eastus",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0
    ):
        """Initialize Azure TTS adapter
        
        Args:
            subscription_key: Azure subscription key
            region: Azure region (e.g., eastus, westus)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_base: Exponential backoff base
        """
        self.subscription_key = subscription_key
        self.region = region
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.default_voice = "en-US-JennyNeural"
        
        # Azure TTS endpoint
        self.endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        
        logger.info("Azure TTS adapter initialized", region=region)
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> AudioResult:
        """Generate audio from text using Azure TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., en-US-JennyNeural)
            speed: Speech speed (0.25-4.0)
            audio_format: Audio format (mp3, wav, ogg)
            
        Returns:
            AudioResult with generated audio
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If Azure API is unreachable
        """
        voice_name = voice or self.default_voice
        
        # Map format to Azure output format
        output_format = self._map_format(audio_format)
        
        # Build SSML
        ssml = self._build_ssml(text, voice_name, speed)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Generating audio with Azure TTS",
                    attempt=attempt + 1,
                    voice=voice_name,
                    speed=speed,
                    format=output_format,
                    text_length=len(text)
                )
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.endpoint,
                        headers={
                            'Ocp-Apim-Subscription-Key': self.subscription_key,
                            'Content-Type': 'application/ssml+xml',
                            'X-Microsoft-OutputFormat': output_format,
                            'User-Agent': 'PillowTalk'
                        },
                        content=ssml,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        audio_data = response.content
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
                            sample_rate=24000,  # Azure uses 24kHz for most formats
                            metadata={
                                'voice': voice_name,
                                'speed': speed,
                                'provider': 'azure',
                                'region': self.region
                            }
                        )
                    elif response.status_code == 401:
                        raise ConfigurationError("Invalid Azure subscription key")
                    elif response.status_code == 429:
                        # Rate limited, retry
                        last_error = Exception(f"Rate limited: {response.text}")
                        logger.warning(
                            "Azure API rate limited, retrying",
                            attempt=attempt + 1,
                            max_retries=self.max_retries
                        )
                        if attempt < self.max_retries - 1:
                            await self._backoff(attempt)
                    else:
                        raise TTSGenerationError(
                            f"Azure TTS API error: {response.status_code} - {response.text}"
                        )
            
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Azure API timeout, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except httpx.ConnectError as e:
                last_error = e
                logger.warning(
                    "Azure API connection error, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except ConfigurationError:
                # Don't retry on configuration errors
                raise
            
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
            f"Azure TTS service unavailable after {self.max_retries} attempts: {last_error}"
        )
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> Iterator[bytes]:
        """Generate audio in streaming mode
        
        Azure TTS doesn't support true streaming in the same way,
        so we fall back to non-streaming and yield the complete audio.
        
        Args:
            text: Text to convert to speech
            voice: Voice name
            speed: Speech speed
            audio_format: Audio format
            
        Yields:
            Audio data chunks
        """
        logger.debug("Azure TTS using non-streaming mode")
        
        result = await self.synthesize(text, voice, speed, audio_format)
        
        # Yield in chunks for consistency with streaming interface
        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
    
    def get_voices(self) -> List[VoiceProfile]:
        """Get available Azure voices
        
        Returns a subset of popular neural voices.
        
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
                provider_specific={'type': 'Neural'}
            ),
            VoiceProfile(
                voice_id="en-US-GuyNeural",
                name="Guy (US)",
                language="en-US",
                gender="male",
                provider_specific={'type': 'Neural'}
            ),
            VoiceProfile(
                voice_id="en-US-AriaNeural",
                name="Aria (US)",
                language="en-US",
                gender="female",
                provider_specific={'type': 'Neural'}
            ),
            # Chinese (Mandarin) voices
            VoiceProfile(
                voice_id="zh-CN-XiaoxiaoNeural",
                name="Xiaoxiao (CN)",
                language="zh-CN",
                gender="female",
                provider_specific={'type': 'Neural'}
            ),
            VoiceProfile(
                voice_id="zh-CN-YunxiNeural",
                name="Yunxi (CN)",
                language="zh-CN",
                gender="male",
                provider_specific={'type': 'Neural'}
            ),
        ]
        return voices
    
    def validate_config(self) -> bool:
        """Validate Azure TTS adapter configuration
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.subscription_key:
            raise ConfigurationError("Azure subscription key is required")
        if not self.region:
            raise ConfigurationError("Azure region is required")
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Azure TTS API health
        
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            # Try a minimal API call to check connectivity
            ssml = self._build_ssml("test", self.default_voice, 1.0)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    headers={
                        'Ocp-Apim-Subscription-Key': self.subscription_key,
                        'Content-Type': 'application/ssml+xml',
                        'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3',
                        'User-Agent': 'PillowTalk'
                    },
                    content=ssml,
                    timeout=10.0
                )
                
                response_time_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'response_time_ms': response_time_ms,
                        'provider': 'azure',
                        'details': {
                            'region': self.region,
                            'service': 'Azure Cognitive Services Speech'
                        }
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'response_time_ms': response_time_ms,
                        'provider': 'azure',
                        'details': {
                            'error': f"HTTP {response.status_code}",
                            'message': response.text
                        }
                    }
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'provider': 'azure',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    async def close(self) -> None:
        """Close Azure TTS adapter"""
        logger.info("Azure TTS adapter closed")
    
    def _map_format(self, format: str) -> str:
        """Map generic format to Azure output format
        
        Args:
            format: Generic format (mp3, wav, ogg)
            
        Returns:
            Azure output format string
        """
        format_map = {
            'mp3': 'audio-24khz-48kbitrate-mono-mp3',
            'wav': 'riff-24khz-16bit-mono-pcm',
            'ogg': 'ogg-24khz-16bit-mono-opus'
        }
        return format_map.get(format, 'audio-24khz-48kbitrate-mono-mp3')
    
    def _build_ssml(self, text: str, voice: str, speed: float) -> str:
        """Build SSML for Azure TTS
        
        Args:
            text: Text to synthesize
            voice: Voice name
            speed: Speech speed multiplier
            
        Returns:
            SSML string
        """
        # Convert speed to prosody rate
        # Azure uses percentage: 1.0 = 100%, 2.0 = 200%, 0.5 = 50%
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
