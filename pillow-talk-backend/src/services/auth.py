"""Authentication service

Provides API key encryption, decryption, and request validation.
"""
from typing import Optional
import structlog
from cryptography.fernet import Fernet, InvalidToken

from ..utils.exceptions import AuthenticationError, ConfigurationError


logger = structlog.get_logger(__name__)


class AuthenticationService:
    """Authentication service for API key management
    
    Provides secure encryption and decryption of API keys using Fernet (AES-256).
    Validates incoming requests and manages authentication state.
    """
    
    def __init__(self, encryption_key: str):
        """Initialize authentication service
        
        Args:
            encryption_key: Base64-encoded Fernet encryption key
            
        Raises:
            ConfigurationError: If encryption key is invalid
        """
        try:
            self.cipher = Fernet(encryption_key.encode())
            logger.info("Authentication service initialized")
        except Exception as e:
            logger.error("Failed to initialize authentication service", error=str(e))
            raise ConfigurationError(f"Invalid encryption key: {e}")
    
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt an API key for secure storage
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Encrypted API key (base64-encoded)
            
        Examples:
            >>> auth = AuthenticationService(encryption_key)
            >>> encrypted = auth.encrypt_api_key("sk-1234567890")
            >>> print(encrypted)
            'gAAAAABh...'
        """
        try:
            encrypted_bytes = self.cipher.encrypt(api_key.encode())
            encrypted_key = encrypted_bytes.decode()
            
            logger.debug("API key encrypted successfully")
            return encrypted_key
        
        except Exception as e:
            logger.error("Failed to encrypt API key", error=str(e))
            raise AuthenticationError(f"Encryption failed: {e}")
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt an encrypted API key
        
        Args:
            encrypted_key: Encrypted API key (base64-encoded)
            
        Returns:
            Plain text API key
            
        Raises:
            AuthenticationError: If decryption fails
            
        Examples:
            >>> auth = AuthenticationService(encryption_key)
            >>> decrypted = auth.decrypt_api_key(encrypted_key)
            >>> print(decrypted)
            'sk-1234567890'
        """
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_key.encode())
            api_key = decrypted_bytes.decode()
            
            logger.debug("API key decrypted successfully")
            return api_key
        
        except InvalidToken:
            logger.error("Invalid encrypted API key or wrong encryption key")
            raise AuthenticationError("Invalid encrypted API key")
        
        except Exception as e:
            logger.error("Failed to decrypt API key", error=str(e))
            raise AuthenticationError(f"Decryption failed: {e}")
    
    def validate_request(
        self,
        api_key: Optional[str] = None,
        require_auth: bool = False
    ) -> bool:
        """Validate an incoming request
        
        Args:
            api_key: API key from request (if provided)
            require_auth: Whether authentication is required
            
        Returns:
            True if request is valid
            
        Raises:
            AuthenticationError: If authentication is required but invalid
            
        Examples:
            >>> auth = AuthenticationService(encryption_key)
            >>> auth.validate_request(api_key="valid-key", require_auth=True)
            True
        """
        if not require_auth:
            # Authentication not required
            logger.debug("Request validation passed (auth not required)")
            return True
        
        if not api_key:
            logger.warning("Authentication required but no API key provided")
            raise AuthenticationError("API key is required")
        
        # Validate API key format
        if not self._is_valid_api_key_format(api_key):
            logger.warning("Invalid API key format", api_key_prefix=api_key[:10])
            raise AuthenticationError("Invalid API key format")
        
        logger.debug("Request validation passed", api_key_prefix=api_key[:10])
        return True
    
    def _is_valid_api_key_format(self, api_key: str) -> bool:
        """Validate API key format
        
        Basic validation to check if API key looks valid.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if format is valid
        """
        # Basic checks
        if not api_key or len(api_key) < 10:
            return False
        
        # Check for common API key prefixes
        valid_prefixes = ['sk-', 'pk-', 'Bearer ', 'api-', 'key-']
        has_valid_prefix = any(api_key.startswith(prefix) for prefix in valid_prefixes)
        
        # If it has a known prefix, it's likely valid
        # Otherwise, check if it's a reasonable length
        if has_valid_prefix:
            return True
        
        # Generic API keys should be at least 20 characters
        return len(api_key) >= 20
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new Fernet encryption key
        
        Returns:
            Base64-encoded encryption key
            
        Examples:
            >>> key = AuthenticationService.generate_encryption_key()
            >>> print(key)
            'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx='
        """
        key = Fernet.generate_key()
        return key.decode()
    
    def rotate_key(self, new_encryption_key: str, encrypted_api_keys: list[str]) -> list[str]:
        """Rotate encryption key and re-encrypt all API keys
        
        Args:
            new_encryption_key: New Fernet encryption key
            encrypted_api_keys: List of API keys encrypted with old key
            
        Returns:
            List of API keys encrypted with new key
            
        Raises:
            AuthenticationError: If rotation fails
            
        Examples:
            >>> auth = AuthenticationService(old_key)
            >>> new_keys = auth.rotate_key(new_key, [encrypted_key1, encrypted_key2])
        """
        try:
            # Create new cipher with new key
            new_cipher = Fernet(new_encryption_key.encode())
            
            # Decrypt with old key and re-encrypt with new key
            re_encrypted_keys = []
            for encrypted_key in encrypted_api_keys:
                # Decrypt with old key
                plain_key = self.decrypt_api_key(encrypted_key)
                
                # Encrypt with new key
                new_encrypted_bytes = new_cipher.encrypt(plain_key.encode())
                new_encrypted_key = new_encrypted_bytes.decode()
                
                re_encrypted_keys.append(new_encrypted_key)
            
            logger.info(
                "Encryption key rotated successfully",
                keys_rotated=len(re_encrypted_keys)
            )
            
            return re_encrypted_keys
        
        except Exception as e:
            logger.error("Failed to rotate encryption key", error=str(e))
            raise AuthenticationError(f"Key rotation failed: {e}")
