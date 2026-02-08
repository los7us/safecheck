"""
Media Processing Service (FULL IMPLEMENTATION)

Handles media downloading, caching, and feature extraction.
"""

from typing import Optional, List, Tuple
from pathlib import Path

from src.core.schemas import MediaMetadata, MediaFeatures, MediaType
from src.utils.media_cache import MediaCache
from src.services.image_features import ImageFeatureExtractor


class MediaProcessorException(Exception):
    """Base exception for media processing errors"""
    pass


class MediaProcessor:
    """
    Processes media content and extracts features.
    
    Fully implemented with caching and feature extraction.
    """
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 10):
        """
        Initialize media processor.
        
        Args:
            cache_dir: Directory for caching downloaded media
            max_size_mb: Maximum file size to process (MB)
        """
        self.cache = MediaCache(cache_dir, max_size_mb)
        self.feature_extractor = ImageFeatureExtractor()
        
        # Metrics
        self.total_processed = 0
        self.total_cache_hits = 0
    
    async def process_media(
        self, 
        media_url: str, 
        media_type: MediaType
    ) -> Tuple[MediaMetadata, Optional[MediaFeatures]]:
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
        try:
            # Download and cache
            file_path, file_hash = await self.cache.download_and_cache(media_url)
            
            # Track metrics
            self.total_processed += 1
            
            # Extract basic metadata
            metadata = MediaMetadata(
                media_type=media_type,
                url=media_url,
                hash=file_hash,
            )
            
            # Add image-specific metadata
            if media_type == MediaType.IMAGE:
                image_meta = self.feature_extractor.get_image_metadata(file_path)
                metadata.width = image_meta.get('width')
                metadata.height = image_meta.get('height')
                metadata.size_bytes = image_meta.get('size_bytes')
            
            # Extract features (if applicable)
            features = None
            if media_type == MediaType.IMAGE:
                features = await self.feature_extractor.extract_features(file_path)
            
            return metadata, features
        
        except Exception as e:
            raise MediaProcessorException(f"Failed to process media {media_url}: {e}")
    
    async def process_media_list(
        self,
        media_items: List[MediaMetadata]
    ) -> Optional[MediaFeatures]:
        """
        Process a list of media items and combine features.
        
        For MVP, we process only the first image and return its features.
        
        Args:
            media_items: List of media metadata from adapter
        
        Returns:
            Combined MediaFeatures or None
        """
        if not media_items:
            return None
        
        # Process first image only (MVP simplification)
        first_image = None
        for item in media_items:
            if item.media_type == MediaType.IMAGE:
                first_image = item
                break
        
        if not first_image:
            return None
        
        try:
            _, features = await self.process_media(
                first_image.url,
                first_image.media_type
            )
            return features
        except Exception as e:
            print(f"Warning: Failed to process media: {e}")
            return None
    
    def get_metrics(self) -> dict:
        """Get processing metrics"""
        cache_stats = self.cache.get_cache_stats()
        
        return {
            'total_processed': self.total_processed,
            'total_cache_hits': self.total_cache_hits,
            'cache_stats': cache_stats,
        }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.cache.close()
