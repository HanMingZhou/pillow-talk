"""Text preprocessing for TTS

Cleans and normalizes text before TTS conversion.
"""
import re
from typing import Pattern
import structlog

from .config import TTSConfig


logger = structlog.get_logger(__name__)


class TextPreprocessor:
    """Preprocesses text before TTS conversion
    
    Handles URL replacement, markdown stripping, code block handling,
    and whitespace normalization based on configuration.
    """
    
    def __init__(self, config: TTSConfig):
        """Initialize text preprocessor
        
        Args:
            config: TTS configuration
        """
        self.config = config
        
        # Compile regex patterns
        self.url_pattern: Pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.code_block_pattern: Pattern = re.compile(
            r'```[\s\S]*?```|`[^`]+`'
        )
    
    def process(self, text: str) -> str:
        """Preprocess text for TTS
        
        Args:
            text: Raw input text
            
        Returns:
            Processed text ready for TTS
        """
        if not text or not text.strip():
            return ""
        
        # Truncate if too long
        if len(text) > self.config.max_text_length:
            logger.warning(
                "Text length exceeds maximum, truncating",
                original_length=len(text),
                max_length=self.config.max_text_length
            )
            text = text[:self.config.max_text_length]
        
        # Handle URLs
        if self.config.url_handling == "replace":
            text = self.url_pattern.sub("link", text)
        elif self.config.url_handling == "remove":
            text = self.url_pattern.sub("", text)
        # 'keep' means do nothing
        
        # Handle code blocks
        if self.config.code_block_handling == "replace":
            text = self.code_block_pattern.sub("code block", text)
        elif self.config.code_block_handling == "skip":
            text = self.code_block_pattern.sub("", text)
        # 'keep' means do nothing
        
        # Strip markdown
        if self.config.strip_markdown:
            text = self._strip_markdown(text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _strip_markdown(self, text: str) -> str:
        """Remove markdown formatting
        
        Args:
            text: Text with markdown formatting
            
        Returns:
            Text without markdown formatting
        """
        # Remove headers
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove inline code (but not code blocks, handled separately)
        # This is already handled by code_block_pattern
        
        return text
