"""TTS system core

Core orchestration for the TTS system.
"""
from typing import Optional
import structlog

from .config import TTSConfig, TTSMode, CloudProvider
from .models import AudioResponse
from .adapters import TTSAdapter
from .adapters.openai_adapter import OpenAIAdapter
from .preprocessor import TextPreprocessor
from .storage import AudioStorage
from ..utils.exceptions import TTSGenerationError, ConfigurationError


logger = structlog.get_logger(__name__)


class TTSSystem:
    """Core TTS system orchestrator
    
    Coordinates text preprocessing, audio generation,
    and storage across different TTS providers.
    """
    
    def __init__(self, config: TTSConfig):
        """Initialize TTS system
        
        Args:
            config: TTS configuration
        """
        self.config = config
        self.text_preprocessor = TextPreprocessor(config)
        self.audio_storage = AudioStorage(config)
        self.adapter = self._create_adapter()
        
        logger.info(
            "TTS system initialized",
            mode=config.mode.value,
            provider=self._get_provider_name()
        )
    
    def _create_adapter(self) -> Optional[TTSAdapter]:
        """Create TTS adapter based on configuration
        
        Returns:
            TTS adapter instance or None for local mode
            
        Raises:
            ConfigurationError: If adapter cannot be created
        """
        if self.config.mode == TTSMode.LOCAL:
            # No adapter needed for local mode
            return None
        
        elif self.config.mode == TTSMode.CLOUD:
            if self.config.cloud_provider == CloudProvider.OPENAI:
                return OpenAIAdapter(
                    api_key=self.config.openai_api_key,
                    timeout=30.0,
                    max_retries=self.config.max_retries,
                    retry_backoff_base=self.config.retry_backoff_base
                )
            elif self.config.cloud_provider == CloudProvider.GOOGLE:
                # TODO: Implement Google Cloud adapter
                raise ConfigurationError(
                    "Google Cloud TTS adapter not yet implemented"
                )
        
        elif self.config.mode == TTSMode.SELF_HOSTED:
            # TODO: Implement self-hosted adapters
            raise ConfigurationError(
                f"Self-hosted TTS adapter for {self.config.self_hosted_provider.value} "
                "not yet implemented"
            )
        
        raise ConfigurationError(f"Unsupported TTS mode: {self.config.mode}")
    
    async def generate_audio(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        audio_format: Optional[str] = None
    ) -> Optional[AudioResponse]:
        """Generate audio from text
        
        Args:
            text: Text to convert to speech
            voice: Voice ID (None for default)
            speed: Speech speed (None for default)
            audio_format: Audio format (None for default)
            
        Returns:
            AudioResponse with URL and metadata, or None if local mode
            
        Raises:
            TTSGenerationError: If generation fails
        """
        # Check if local mode
        if self.config.mode == TTSMode.LOCAL:
            logger.info("TTS in local mode, skipping audio generation")
            return None
        
        # Preprocess text
        processed_text = self.text_preprocessor.process(text)
        
        if not processed_text:
            raise TTSGenerationError("Text is empty after preprocessing")
        
        # Use defaults if not specified
        voice = voice or self.config.default_voice
        speed = speed or self.config.default_speed
        audio_format = audio_format or self.config.default_format
        
        # Validate and clamp parameters
        speed = self._validate_speed(speed)
        voice = self._validate_voice(voice)
        
        logger.info(
            "Generating audio",
            text_length=len(processed_text),
            voice=voice,
            speed=speed,
            format=audio_format
        )
        
        # Generate audio
        audio_result = await self.adapter.synthesize(
            text=processed_text,
            voice=voice,
            speed=speed,
            audio_format=audio_format
        )
        
        # Store audio
        audio_url = self.audio_storage.store_audio(
            audio_data=audio_result.audio_data,
            format=audio_result.format,
            metadata={
                'duration': audio_result.duration,
                'voice': voice,
                'speed': speed,
                'text_length': len(text),
                'sample_rate': audio_result.sample_rate,
                **audio_result.metadata
            }
        )
        
        logger.info(
            "Audio generated and stored",
            url=audio_url,
            duration=audio_result.duration
        )
        
        return AudioResponse(
            audio_url=audio_url,
            duration=audio_result.duration,
            format=audio_result.format,
            voice=voice,
            speed=speed
        )
    
    async def generate_audio_streaming(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        audio_format: Optional[str] = None
    ):
        """Generate audio in streaming mode
        
        Args:
            text: Text to convert to speech
            voice: Voice ID
            speed: Speech speed
            audio_format: Audio format
            
        Yields:
            Audio data chunks
            
        Raises:
            TTSGenerationError: If streaming not available or fails
        """
        if self.config.mode == TTSMode.LOCAL:
            raise TTSGenerationError("Streaming not available in local mode")
        
        # Preprocess text
        processed_text = self.text_preprocessor.process(text)
        
        if not processed_text:
            raise TTSGenerationError("Text is empty after preprocessing")
        
        # Use defaults
        voice = voice or self.config.default_voice
        speed = speed or self.config.default_speed
        audio_format = audio_format or self.config.default_format
        
        # Validate parameters
        speed = self._validate_speed(speed)
        voice = self._validate_voice(voice)
        
        logger.info(
            "Starting streaming audio generation",
            text_length=len(processed_text),
            voice=voice,
            speed=speed
        )
        
        async for chunk in self.adapter.synthesize_streaming(
            text=processed_text,
            voice=voice,
            speed=speed,
            audio_format=audio_format
        ):
            yield chunk
    
    def _validate_speed(self, speed: float) -> float:
        """Validate and clamp speed parameter
        
        Args:
            speed: Requested speed
            
        Returns:
            Validated speed (clamped to 0.25-4.0)
        """
        if speed < 0.25:
            logger.warning(
                "Speed too low, clamping to minimum",
                requested=speed,
                clamped=0.25
            )
            return 0.25
        
        if speed > 4.0:
            logger.warning(
                "Speed too high, clamping to maximum",
                requested=speed,
                clamped=4.0
            )
            return 4.0
        
        return speed
    
    def _validate_voice(self, voice: str) -> str:
        """Validate voice parameter
        
        Args:
            voice: Requested voice
            
        Returns:
            Validated voice (falls back to default if invalid)
        """
        if not self.adapter:
            return voice
        
        available_voices = self.adapter.get_voices()
        voice_ids = [v.voice_id for v in available_voices]
        
        if voice not in voice_ids:
            logger.warning(
                "Voice not available, using default",
                requested=voice,
                default=self.config.default_voice
            )
            return self.config.default_voice
        
        return voice
    
    async def health_check(self):
        """Check TTS system health
        
        Returns:
            Health check result
        """
        if self.config.mode == TTSMode.LOCAL:
            return {
                'status': 'healthy',
                'mode': 'local',
                'provider': 'local',
                'response_time_ms': 0
            }
        
        if not self.adapter:
            return {
                'status': 'unhealthy',
                'mode': self.config.mode.value,
                'provider': self._get_provider_name(),
                'details': {'error': 'No adapter available'}
            }
        
        return await self.adapter.health_check()
    
    async def close(self) -> None:
        """Close TTS system and cleanup resources"""
        if self.adapter:
            await self.adapter.close()
        logger.info("TTS system closed")
    
    def _get_provider_name(self) -> str:
        """Get provider name for logging"""
        if self.config.mode == TTSMode.LOCAL:
            return "local"
        elif self.config.mode == TTSMode.CLOUD:
            return self.config.cloud_provider.value if self.config.cloud_provider else "unknown"
        elif self.config.mode == TTSMode.SELF_HOSTED:
            return self.config.self_hosted_provider.value if self.config.self_hosted_provider else "unknown"
        return "unknown"
