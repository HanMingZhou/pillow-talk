"""Audio cleanup service

Background service for cleaning up expired audio files.
"""
import time
import json
from datetime import datetime, timedelta
from threading import Thread
from typing import Optional
import schedule
import structlog

from .config import TTSConfig
from .storage import AudioStorage


logger = structlog.get_logger(__name__)


class AudioCleanupService:
    """Background service for cleaning up expired audio files
    
    Runs periodically to remove audio files older than
    the configured expiration time.
    """
    
    def __init__(self, audio_storage: AudioStorage, config: TTSConfig):
        """Initialize cleanup service
        
        Args:
            audio_storage: Audio storage instance
            config: TTS configuration
        """
        self.audio_storage = audio_storage
        self.config = config
        self.running = False
        self.thread: Optional[Thread] = None
        
        logger.info(
            "Audio cleanup service initialized",
            expiration_hours=config.audio_expiration_hours,
            interval_hours=config.cleanup_interval_hours
        )
    
    def start(self) -> None:
        """Start the cleanup service"""
        if self.running:
            logger.warning("Cleanup service already running")
            return
        
        self.running = True
        
        # Schedule cleanup task
        schedule.every(self.config.cleanup_interval_hours).hours.do(
            self.cleanup
        )
        
        # Start background thread
        self.thread = Thread(target=self._run_schedule, daemon=True)
        self.thread.start()
        
        logger.info("Audio cleanup service started")
    
    def stop(self) -> None:
        """Stop the cleanup service"""
        if not self.running:
            return
        
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        schedule.clear()
        
        logger.info("Audio cleanup service stopped")
    
    def _run_schedule(self) -> None:
        """Run scheduled tasks in background thread"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def cleanup(self) -> None:
        """Remove expired audio files
        
        Scans all metadata files and deletes files older
        than the configured expiration time.
        """
        logger.info("Starting audio cleanup")
        
        cutoff_time = datetime.utcnow() - timedelta(
            hours=self.config.audio_expiration_hours
        )
        
        deleted_count = 0
        error_count = 0
        
        # Scan all metadata files
        for metadata_file in self.audio_storage.storage_path.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                created_at = datetime.fromisoformat(metadata['created_at'])
                
                if created_at < cutoff_time:
                    file_id = metadata_file.stem
                    
                    if self.audio_storage.delete_file(file_id):
                        deleted_count += 1
                        logger.debug(
                            "Deleted expired audio file",
                            file_id=file_id,
                            created_at=created_at.isoformat()
                        )
            
            except Exception as e:
                error_count += 1
                logger.error(
                    "Error cleaning up audio file",
                    file=str(metadata_file),
                    error=str(e)
                )
        
        logger.info(
            "Audio cleanup completed",
            deleted=deleted_count,
            errors=error_count,
            cutoff_time=cutoff_time.isoformat()
        )
