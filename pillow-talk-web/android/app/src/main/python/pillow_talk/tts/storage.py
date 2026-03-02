"""Audio storage service

Manages audio file storage and URL generation.
"""
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import structlog

from .config import TTSConfig


logger = structlog.get_logger(__name__)


class AudioStorage:
    """Manages audio file storage and URL generation
    
    Handles saving audio files to local or cloud storage,
    generating accessible URLs, and managing metadata.
    """
    
    def __init__(self, config: TTSConfig):
        """Initialize audio storage
        
        Args:
            config: TTS configuration
        """
        self.config = config
        self.storage_path = Path(config.local_storage_path)
        
        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            "Audio storage initialized",
            storage_type=config.storage_type,
            path=str(self.storage_path)
        )
    
    def store_audio(
        self,
        audio_data: bytes,
        format: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Store audio file and return URL
        
        Args:
            audio_data: Raw audio bytes
            format: Audio format (mp3, wav, ogg)
            metadata: Audio metadata to store
            
        Returns:
            URL to access the audio file
        """
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.{format}"
        filepath = self.storage_path / filename
        
        # Write audio file
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        # Write metadata sidecar
        metadata_path = self.storage_path / f"{file_id}.json"
        metadata['created_at'] = datetime.utcnow().isoformat()
        metadata['filename'] = filename
        metadata['size_bytes'] = len(audio_data)
        metadata['format'] = format
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Generate URL
        if self.config.storage_type == "local":
            audio_url = f"{self.config.base_url}/audio/{filename}"
        else:
            # Upload to cloud storage and return cloud URL
            audio_url = self._upload_to_cloud(filepath, filename)
        
        logger.info(
            "Audio file stored",
            file_id=file_id,
            format=format,
            size_bytes=len(audio_data),
            url=audio_url
        )
        
        return audio_url
    
    def _upload_to_cloud(self, filepath: Path, filename: str) -> str:
        """Upload file to cloud storage
        
        Args:
            filepath: Local file path
            filename: Filename to use in cloud storage
            
        Returns:
            Cloud storage URL
            
        Note:
            This is a placeholder for cloud storage implementation.
            Implement S3/GCS upload logic here.
        """
        # TODO: Implement cloud storage upload
        # For now, fall back to local URL
        logger.warning(
            "Cloud storage not yet implemented, using local storage",
            filename=filename
        )
        return f"{self.config.base_url}/audio/{filename}"
    
    def get_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for an audio file
        
        Args:
            file_id: UUID of the audio file
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self.storage_path / f"{file_id}.json"
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(
                "Failed to read metadata",
                file_id=file_id,
                error=str(e)
            )
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete audio file and metadata
        
        Args:
            file_id: UUID of the audio file
            
        Returns:
            True if file was deleted, False otherwise
        """
        deleted = False
        
        # Find and delete audio file
        for ext in ['mp3', 'wav', 'ogg']:
            audio_path = self.storage_path / f"{file_id}.{ext}"
            if audio_path.exists():
                try:
                    audio_path.unlink()
                    deleted = True
                    logger.debug(
                        "Deleted audio file",
                        file_id=file_id,
                        format=ext
                    )
                except Exception as e:
                    logger.error(
                        "Failed to delete audio file",
                        file_id=file_id,
                        error=str(e)
                    )
        
        # Delete metadata
        metadata_path = self.storage_path / f"{file_id}.json"
        if metadata_path.exists():
            try:
                metadata_path.unlink()
                logger.debug(
                    "Deleted metadata file",
                    file_id=file_id
                )
            except Exception as e:
                logger.error(
                    "Failed to delete metadata file",
                    file_id=file_id,
                    error=str(e)
                )
        
        return deleted
    
    def get_content_type(self, format: str) -> str:
        """Get Content-Type header for audio format
        
        Args:
            format: Audio format (mp3, wav, ogg)
            
        Returns:
            Content-Type string
        """
        content_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'ogg': 'audio/ogg'
        }
        return content_types.get(format, 'application/octet-stream')
