"""TTS adapters module

Factory for creating TTS adapter instances based on provider.
"""
from typing import Optional
import structlog

from .base import TTSAdapter
from .openai_adapter import OpenAIAdapter
from ...utils.exceptions import ConfigurationError

# Optional imports for TTS providers
try:
    from .google_adapter import GoogleTTSAdapter
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    GoogleTTSAdapter = None

try:
    from .azure_adapter import AzureTTSAdapter
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    AzureTTSAdapter = None

try:
    from .edge_adapter import EdgeTTSAdapter
    EDGE_AVAILABLE = True
except ImportError:
    EDGE_AVAILABLE = False
    EdgeTTSAdapter = None

try:
    from .ali_adapter import AliTTSAdapter
    ALI_AVAILABLE = True
except ImportError:
    ALI_AVAILABLE = False
    AliTTSAdapter = None


logger = structlog.get_logger(__name__)


class TTSAdapterFactory:
    """Factory for creating TTS adapter instances
    
    Creates appropriate TTS adapter based on provider name and configuration.
    """
    
    @staticmethod
    def create_adapter(
        provider: str,
        config: dict
    ) -> TTSAdapter:
        """Create TTS adapter instance
        
        Args:
            provider: Provider name (openai, google, azure, edge, alibaba)
            config: Provider-specific configuration dictionary
            
        Returns:
            TTSAdapter instance
            
        Raises:
            ConfigurationError: If provider is unsupported or config is invalid
            
        Examples:
            >>> factory = TTSAdapterFactory()
            >>> adapter = factory.create_adapter('openai', {'api_key': 'sk-...'})
            >>> adapter = factory.create_adapter('google', {'credentials_path': '/path/to/creds.json'})
        """
        provider = provider.lower()
        
        logger.info("Creating TTS adapter", provider=provider)
        
        try:
            if provider == 'openai':
                return TTSAdapterFactory._create_openai_adapter(config)
            elif provider == 'google':
                if not GOOGLE_AVAILABLE:
                    raise ConfigurationError(
                        "Google TTS is not available. Install with: pip install google-cloud-texttospeech"
                    )
                return TTSAdapterFactory._create_google_adapter(config)
            elif provider == 'azure':
                if not AZURE_AVAILABLE:
                    raise ConfigurationError(
                        "Azure TTS is not available. Install with: pip install azure-cognitiveservices-speech"
                    )
                return TTSAdapterFactory._create_azure_adapter(config)
            elif provider == 'edge':
                if not EDGE_AVAILABLE:
                    raise ConfigurationError(
                        "Edge TTS is not available. Install with: pip install edge-tts"
                    )
                return TTSAdapterFactory._create_edge_adapter(config)
            elif provider in ['alibaba', 'aliyun', 'ali']:
                if not ALI_AVAILABLE:
                    raise ConfigurationError(
                        "Alibaba TTS is not available. Install with: pip install alibabacloud-nls-python-sdk"
                    )
                return TTSAdapterFactory._create_ali_adapter(config)
            else:
                raise ConfigurationError(
                    f"Unsupported TTS provider: {provider}. "
                    f"Supported providers: openai, google, azure, edge, alibaba"
                )
        except KeyError as e:
            raise ConfigurationError(
                f"Missing required configuration for {provider}: {e}"
            )
        except Exception as e:
            logger.error(
                "Failed to create TTS adapter",
                provider=provider,
                error=str(e)
            )
            raise ConfigurationError(
                f"Failed to create {provider} TTS adapter: {e}"
            )
    
    @staticmethod
    def _create_openai_adapter(config: dict) -> OpenAIAdapter:
        """Create OpenAI TTS adapter
        
        Required config:
            - api_key: OpenAI API key
            
        Optional config:
            - timeout: Request timeout (default: 30.0)
            - max_retries: Maximum retry attempts (default: 3)
            - retry_backoff_base: Exponential backoff base (default: 2.0)
        """
        return OpenAIAdapter(
            api_key=config['api_key'],
            timeout=config.get('timeout', 30.0),
            max_retries=config.get('max_retries', 3),
            retry_backoff_base=config.get('retry_backoff_base', 2.0)
        )
    
    @staticmethod
    def _create_google_adapter(config: dict) -> GoogleTTSAdapter:
        """Create Google Cloud TTS adapter
        
        Optional config:
            - credentials_path: Path to Google Cloud credentials JSON
            - timeout: Request timeout (default: 30.0)
            - max_retries: Maximum retry attempts (default: 3)
            - retry_backoff_base: Exponential backoff base (default: 2.0)
        """
        return GoogleTTSAdapter(
            credentials_path=config.get('credentials_path'),
            timeout=config.get('timeout', 30.0),
            max_retries=config.get('max_retries', 3),
            retry_backoff_base=config.get('retry_backoff_base', 2.0)
        )
    
    @staticmethod
    def _create_azure_adapter(config: dict) -> AzureTTSAdapter:
        """Create Azure TTS adapter
        
        Required config:
            - subscription_key: Azure subscription key
            
        Optional config:
            - region: Azure region (default: eastus)
            - timeout: Request timeout (default: 30.0)
            - max_retries: Maximum retry attempts (default: 3)
            - retry_backoff_base: Exponential backoff base (default: 2.0)
        """
        return AzureTTSAdapter(
            subscription_key=config['subscription_key'],
            region=config.get('region', 'eastus'),
            timeout=config.get('timeout', 30.0),
            max_retries=config.get('max_retries', 3),
            retry_backoff_base=config.get('retry_backoff_base', 2.0)
        )
    
    @staticmethod
    def _create_edge_adapter(config: dict) -> EdgeTTSAdapter:
        """Create Edge TTS adapter
        
        Optional config:
            - timeout: Request timeout (default: 30.0)
            - max_retries: Maximum retry attempts (default: 3)
            - retry_backoff_base: Exponential backoff base (default: 2.0)
        """
        return EdgeTTSAdapter(
            timeout=config.get('timeout', 30.0),
            max_retries=config.get('max_retries', 3),
            retry_backoff_base=config.get('retry_backoff_base', 2.0)
        )
    
    @staticmethod
    def _create_ali_adapter(config: dict) -> AliTTSAdapter:
        """Create Alibaba Cloud TTS adapter
        
        Required config:
            - access_key_id: Alibaba Cloud access key ID
            - access_key_secret: Alibaba Cloud access key secret
            - app_key: Speech synthesis app key
            
        Optional config:
            - region: Alibaba Cloud region (default: cn-shanghai)
            - timeout: Request timeout (default: 30.0)
            - max_retries: Maximum retry attempts (default: 3)
            - retry_backoff_base: Exponential backoff base (default: 2.0)
        """
        return AliTTSAdapter(
            access_key_id=config['access_key_id'],
            access_key_secret=config['access_key_secret'],
            app_key=config['app_key'],
            region=config.get('region', 'cn-shanghai'),
            timeout=config.get('timeout', 30.0),
            max_retries=config.get('max_retries', 3),
            retry_backoff_base=config.get('retry_backoff_base', 2.0)
        )


__all__ = [
    'TTSAdapter',
    'TTSAdapterFactory',
    'OpenAIAdapter',
    'GoogleTTSAdapter',
    'AzureTTSAdapter',
    'EdgeTTSAdapter',
    'AliTTSAdapter',
]
