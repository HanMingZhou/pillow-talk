"""Alibaba Cloud TTS adapter

Adapter for Alibaba Cloud (Aliyun) Text-to-Speech API.
"""
import time
import json
from typing import List, Dict, Any, Optional, Iterator
import structlog
import httpx
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import quote

from .base import TTSAdapter
from ..models import AudioResult, VoiceProfile
from ...utils.exceptions import (
    TTSGenerationError,
    TTSProviderUnavailableError,
    ConfigurationError
)


logger = structlog.get_logger(__name__)


class AliTTSAdapter(TTSAdapter):
    """Alibaba Cloud TTS adapter
    
    Implements TTS using Alibaba Cloud (Aliyun) Speech Synthesis API.
    Supports multiple Chinese and English voices.
    """
    
    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        app_key: str,
        region: str = "cn-shanghai",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0
    ):
        """Initialize Alibaba Cloud TTS adapter
        
        Args:
            access_key_id: Alibaba Cloud access key ID
            access_key_secret: Alibaba Cloud access key secret
            app_key: Speech synthesis app key
            region: Alibaba Cloud region
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_backoff_base: Exponential backoff base
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.app_key = app_key
        self.region = region
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.default_voice = "xiaoyun"  # Female Chinese voice
        
        # Alibaba Cloud TTS endpoint
        self.endpoint = f"https://nls-gateway-{region}.aliyuncs.com/stream/v1/tts"
        
        logger.info("Alibaba Cloud TTS adapter initialized", region=region)
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> AudioResult:
        """Generate audio from text using Alibaba Cloud TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice name (e.g., xiaoyun, xiaogang)
            speed: Speech speed (-500 to 500, 0 is normal)
            audio_format: Audio format (mp3, wav, pcm)
            
        Returns:
            AudioResult with generated audio
            
        Raises:
            TTSGenerationError: If generation fails
            TTSProviderUnavailableError: If Alibaba Cloud API is unreachable
        """
        voice_name = voice or self.default_voice
        
        # Convert speed from multiplier to Alibaba Cloud format (-500 to 500)
        # 1.0 = 0, 2.0 = 500, 0.5 = -250
        ali_speed = int((speed - 1.0) * 500)
        ali_speed = max(-500, min(500, ali_speed))
        
        # Map format
        ali_format = self._map_format(audio_format)
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    "Generating audio with Alibaba Cloud TTS",
                    attempt=attempt + 1,
                    voice=voice_name,
                    speed=ali_speed,
                    format=ali_format,
                    text_length=len(text)
                )
                
                # Build request parameters
                params = {
                    'appkey': self.app_key,
                    'text': text,
                    'voice': voice_name,
                    'format': ali_format,
                    'speech_rate': ali_speed,
                    'volume': 50,  # Default volume (0-100)
                    'sample_rate': 24000
                }
                
                # Generate signature
                headers = self._generate_headers()
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.endpoint,
                        params=params,
                        headers=headers,
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
                            sample_rate=24000,
                            metadata={
                                'voice': voice_name,
                                'speed': speed,
                                'provider': 'alibaba',
                                'region': self.region
                            }
                        )
                    elif response.status_code == 401:
                        raise ConfigurationError("Invalid Alibaba Cloud credentials")
                    elif response.status_code == 429:
                        # Rate limited, retry
                        last_error = Exception(f"Rate limited: {response.text}")
                        logger.warning(
                            "Alibaba Cloud API rate limited, retrying",
                            attempt=attempt + 1,
                            max_retries=self.max_retries
                        )
                        if attempt < self.max_retries - 1:
                            await self._backoff(attempt)
                    else:
                        error_msg = response.text
                        try:
                            error_data = response.json()
                            error_msg = error_data.get('message', error_msg)
                        except:
                            pass
                        raise TTSGenerationError(
                            f"Alibaba Cloud TTS API error: {response.status_code} - {error_msg}"
                        )
            
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    "Alibaba Cloud API timeout, retrying",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await self._backoff(attempt)
            
            except httpx.ConnectError as e:
                last_error = e
                logger.warning(
                    "Alibaba Cloud API connection error, retrying",
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
            f"Alibaba Cloud TTS service unavailable after {self.max_retries} attempts: {last_error}"
        )
    
    async def synthesize_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        audio_format: str = 'mp3'
    ) -> Iterator[bytes]:
        """Generate audio in streaming mode
        
        Alibaba Cloud TTS supports streaming.
        
        Args:
            text: Text to convert to speech
            voice: Voice name
            speed: Speech speed
            audio_format: Audio format
            
        Yields:
            Audio data chunks
        """
        logger.debug("Alibaba Cloud TTS streaming mode")
        
        result = await self.synthesize(text, voice, speed, audio_format)
        
        # Yield in chunks for consistency with streaming interface
        chunk_size = 4096
        audio_data = result.audio_data
        for i in range(0, len(audio_data), chunk_size):
            yield audio_data[i:i + chunk_size]
    
    def get_voices(self) -> List[VoiceProfile]:
        """Get available Alibaba Cloud voices
        
        Returns a subset of popular voices.
        
        Returns:
            List of voice profiles
        """
        voices = [
            # Chinese voices
            VoiceProfile(
                voice_id="xiaoyun",
                name="Xiaoyun (小云)",
                language="zh-CN",
                gender="female",
                provider_specific={'type': 'Standard'}
            ),
            VoiceProfile(
                voice_id="xiaogang",
                name="Xiaogang (小刚)",
                language="zh-CN",
                gender="male",
                provider_specific={'type': 'Standard'}
            ),
            VoiceProfile(
                voice_id="ruoxi",
                name="Ruoxi (若兮)",
                language="zh-CN",
                gender="female",
                provider_specific={'type': 'Premium'}
            ),
            # English voices
            VoiceProfile(
                voice_id="emily",
                name="Emily",
                language="en-US",
                gender="female",
                provider_specific={'type': 'Standard'}
            ),
            VoiceProfile(
                voice_id="harry",
                name="Harry",
                language="en-US",
                gender="male",
                provider_specific={'type': 'Standard'}
            ),
        ]
        return voices
    
    def validate_config(self) -> bool:
        """Validate Alibaba Cloud TTS adapter configuration
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.access_key_id:
            raise ConfigurationError("Alibaba Cloud access key ID is required")
        if not self.access_key_secret:
            raise ConfigurationError("Alibaba Cloud access key secret is required")
        if not self.app_key:
            raise ConfigurationError("Alibaba Cloud app key is required")
        
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Alibaba Cloud TTS API health
        
        Returns:
            Health check result
        """
        start_time = time.time()
        
        try:
            # Try a minimal API call to check connectivity
            await self.synthesize("测试", self.default_voice, 1.0, 'mp3')
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time_ms,
                'provider': 'alibaba',
                'details': {
                    'region': self.region,
                    'service': 'Alibaba Cloud Speech Synthesis'
                }
            }
        
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            return {
                'status': 'unhealthy',
                'response_time_ms': response_time_ms,
                'provider': 'alibaba',
                'details': {
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            }
    
    async def close(self) -> None:
        """Close Alibaba Cloud TTS adapter"""
        logger.info("Alibaba Cloud TTS adapter closed")
    
    def _map_format(self, format: str) -> str:
        """Map generic format to Alibaba Cloud format
        
        Args:
            format: Generic format (mp3, wav, pcm)
            
        Returns:
            Alibaba Cloud format string
        """
        format_map = {
            'mp3': 'mp3',
            'wav': 'wav',
            'ogg': 'mp3'  # Fallback to mp3 for ogg
        }
        return format_map.get(format, 'mp3')
    
    def _generate_headers(self) -> Dict[str, str]:
        """Generate authentication headers for Alibaba Cloud API
        
        Returns:
            Headers dictionary
        """
        # Alibaba Cloud uses a simple token-based authentication
        # In production, you might need to implement full signature v3
        headers = {
            'Content-Type': 'application/json',
            'X-NLS-Token': self._generate_token()
        }
        return headers
    
    def _generate_token(self) -> str:
        """Generate authentication token
        
        Note: This is a simplified implementation.
        In production, you should use the official Alibaba Cloud SDK
        or implement the full authentication flow.
        
        Returns:
            Authentication token
        """
        # Placeholder: In production, use proper token generation
        # via Alibaba Cloud STS or RAM
        return f"{self.access_key_id}:{self.access_key_secret}"
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length
        
        For Chinese text, estimate ~4 characters per second at normal speed
        For English text, estimate ~150 words per minute at normal speed
        
        Args:
            text: Input text
            speed: Speech speed multiplier
            
        Returns:
            Estimated duration in seconds
        """
        # Check if text is primarily Chinese
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        
        if chinese_chars > len(text) / 2:
            # Chinese text: ~4 characters per second
            chars_per_second = 4 * speed
            duration = len(text) / chars_per_second
        else:
            # English text: ~150 words per minute
            word_count = len(text.split())
            words_per_minute = 150 * speed
            duration = (word_count / words_per_minute) * 60
        
        return duration
    
    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff delay
        
        Args:
            attempt: Current attempt number (0-indexed)
        """
        import asyncio
        delay = self.retry_backoff_base ** attempt
        logger.debug(f"Backing off for {delay} seconds")
        await asyncio.sleep(delay)
