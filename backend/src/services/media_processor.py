"""
Media Processing Interface

Handles downloading, caching, and feature extraction from media content.

Responsibilities:
- Download and cache media files
- Generate media hashes for deduplication
- Extract features (captions, OCR, object detection)
- Thumbnail generation
- Size and format validation

Does NOT:
- Store media permanently (only cache)
- Send full images to Gemini (only derived features)
"""

from typing import Optional, Tuple
from pathlib import Path
from src.core.schemas import MediaMetadata, MediaFeatures, MediaType


class MediaProcessorException(Exception):
    """Base exception for media processing errors"""
    pass


class MediaDownloadError(MediaProcessorException):
    """Raised when media cannot be downloaded"""
    pass


class MediaTooLargeError(MediaProcessorException):
    """Raised when media exceeds size limit"""
    pass


class MediaProcessor:
    """
    Processes media content and extracts features.
    
    This class handles all media-related operations for the pipeline.
    """
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 10):
        """
        Initialize media processor.
        
        Args:
            cache_dir: Directory for caching downloaded media
            max_size_mb: Maximum file size to process (MB)
        """
        self.cache_dir = cache_dir
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_media(self, media_url: str, media_type: MediaType) -> Tuple[MediaMetadata, Optional[MediaFeatures]]:
        """
        Download and process a single media item.
        
        Args:
            media_url: URL of media to process
            media_type: Type of media (image, video, etc.)
        
        Returns:
            Tuple of (MediaMetadata, MediaFeatures or None)
        
        Raises:
            MediaProcessorException: If processing fails
        """
        # Download and cache
        file_path, file_hash = await self._download_and_cache(media_url)
        
        # Extract metadata
        metadata = await self._extract_metadata(file_path, media_url, media_type, file_hash)
        
        # Extract features (if applicable)
        features = None
        if media_type == MediaType.IMAGE:
            features = await self._extract_image_features(file_path)
        
        return metadata, features
    
    async def _download_and_cache(self, url: str) -> Tuple[Path, str]:
        """
        Download media and cache it.
        
        Returns:
            Tuple of (cached_file_path, content_hash)
        """
        # To be implemented with actual download logic
        raise NotImplementedError("Download logic to be implemented in Day 3")
    
    async def _extract_metadata(self, file_path: Path, url: str, media_type: MediaType, file_hash: str) -> MediaMetadata:
        """Extract basic metadata from media file"""
        raise NotImplementedError("Metadata extraction to be implemented in Day 3")
    
    async def _extract_image_features(self, file_path: Path) -> MediaFeatures:
        """
        Extract features from image.
        
        - Image captioning (short description)
        - OCR (extract text)
        - Object detection (optional)
        """
        raise NotImplementedError("Feature extraction to be implemented in Day 3")
    
    def get_cache_path(self, content_hash: str) -> Path:
        """Get cache file path from content hash"""
        return self.cache_dir / f"{content_hash[:2]}" / f"{content_hash}.cached"
    
    def is_cached(self, content_hash: str) -> bool:
        """Check if media is already cached"""
        return self.get_cache_path(content_hash).exists()
    
    async def cleanup_cache(self, max_age_hours: int = 24) -> int:
        """
        Remove cached files older than max_age_hours.
        
        Returns:
            Number of files removed
        """
        # To be implemented
        raise NotImplementedError("Cache cleanup to be implemented in Day 3")
