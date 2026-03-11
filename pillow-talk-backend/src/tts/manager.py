"""TTS configuration manager

Manages loading, validation, and access to TTS configuration.
"""
import yaml
import json
from pathlib import Path
from typing import Dict, Any
import httpx
import structlog

from .config import TTSConfig, TTSMode, CloudProvider
from ..utils.exceptions import ConfigurationError


logger = structlog.get_logger(__name__)


class ConfigurationManager:
    """Manages TTS configuration and validation
    
    Loads configuration from file and validates all settings
    at startup to fail fast on misconfiguration.
    """
    
    def __init__(self, config_path: str | None = None, config_dict: Dict[str, Any] | None = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            config_dict: Configuration dictionary (for testing or direct config)
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if config_dict:
            self.config = TTSConfig(**config_dict)
        elif config_path:
            self.config = self._load_config(config_path)
        else:
            raise ConfigurationError("Either config_path or config_dict must be provided")
        
        self.validate_config()
        logger.info(
            "TTS configuration loaded",
            mode=self.config.mode.value,
            provider=self._get_provider_name()
        )
    
    def _load_config(self, path: str) -> TTSConfig:
        """Load configuration from file
        
        Args:
            path: Path to configuration file
            
        Returns:
            TTSConfig instance
            
        Raises:
            ConfigurationError: If file cannot be loaded or parsed
        """
        config_file = Path(path)
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")
        
        try:
            with open(config_file, 'r') as f:
                if config_file.suffix in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                elif config_file.suffix == '.json':
                    config_data = json.load(f)
                else:
                    raise ConfigurationError(
                        f"Unsupported configuration file format: {config_file.suffix}. "
                        "Use .yaml, .yml, or .json"
                    )
            
            # Extract TTS config if nested
            if 'tts' in config_data:
                config_data = config_data['tts']
            
            return TTSConfig(**config_data)
        
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse YAML configuration: {e}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Failed to parse JSON configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def validate_config(self) -> None:
        """Validate configuration at startup
        
        Performs comprehensive validation including:
        - Mode-specific requirements
        - API key presence for cloud providers
        - Endpoint reachability for self-hosted providers
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Pydantic handles basic validation
        # Additional checks based on mode
        
        if self.config.mode == TTSMode.CLOUD:
            self._validate_cloud_config()
        elif self.config.mode == TTSMode.SELF_HOSTED:
            self._validate_self_hosted_config()
        elif self.config.mode == TTSMode.LOCAL:
            logger.info("TTS configured for local mode (client-side)")
        
        # Validate storage configuration
        if self.config.storage_type == "cloud" and not self.config.cloud_storage_bucket:
            raise ConfigurationError(
                "cloud_storage_bucket is required when storage_type is 'cloud'"
            )
        
        logger.info("TTS configuration validation passed")
    
    def _validate_cloud_config(self) -> None:
        """Validate cloud provider configuration
        
        Raises:
            ConfigurationError: If cloud configuration is invalid
        """
        if self.config.cloud_provider == CloudProvider.OPENAI:
            if not self.config.openai_api_key:
                raise ConfigurationError(
                    "openai_api_key is required when cloud_provider is 'openai'. "
                    "Set OPENAI_API_KEY environment variable or provide in config."
                )
            logger.info("OpenAI TTS configuration validated")
        
        elif self.config.cloud_provider == CloudProvider.GOOGLE:
            if not self.config.google_credentials_path:
                raise ConfigurationError(
                    "google_credentials_path is required when cloud_provider is 'google'. "
                    "Provide path to Google Cloud credentials JSON file."
                )
            
            # Check if credentials file exists
            creds_path = Path(self.config.google_credentials_path)
            if not creds_path.exists():
                raise ConfigurationError(
                    f"Google Cloud credentials file not found: {self.config.google_credentials_path}"
                )
            
            logger.info("Google Cloud TTS configuration validated")
    
    def _validate_self_hosted_config(self) -> None:
        """Validate self-hosted configuration
        
        Tests connectivity to the self-hosted endpoint.
        
        Raises:
            ConfigurationError: If self-hosted configuration is invalid
        """
        if not self.config.self_hosted_endpoint:
            raise ConfigurationError(
                "self_hosted_endpoint is required when mode is 'self-hosted'. "
                "Provide the URL of your self-hosted TTS service."
            )
        
        # Test connectivity to self-hosted endpoint
        try:
            logger.info(
                "Testing connectivity to self-hosted TTS service",
                endpoint=self.config.self_hosted_endpoint
            )
            
            response = httpx.get(
                f"{self.config.self_hosted_endpoint}/health",
                timeout=10.0
            )
            response.raise_for_status()
            
            logger.info(
                "Self-hosted TTS service is reachable",
                provider=self.config.self_hosted_provider.value,
                status_code=response.status_code
            )
        
        except httpx.TimeoutException:
            raise ConfigurationError(
                f"Self-hosted TTS service at {self.config.self_hosted_endpoint} "
                "timed out. Ensure the service is running and accessible."
            )
        except httpx.HTTPError as e:
            raise ConfigurationError(
                f"Cannot reach self-hosted TTS service at {self.config.self_hosted_endpoint}: {e}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to validate self-hosted TTS configuration: {e}"
            )
    
    def _get_provider_name(self) -> str:
        """Get the provider name for logging
        
        Returns:
            Provider name string
        """
        if self.config.mode == TTSMode.LOCAL:
            return "local"
        elif self.config.mode == TTSMode.CLOUD:
            return self.config.cloud_provider.value if self.config.cloud_provider else "unknown"
        elif self.config.mode == TTSMode.SELF_HOSTED:
            return self.config.self_hosted_provider.value if self.config.self_hosted_provider else "unknown"
        return "unknown"
