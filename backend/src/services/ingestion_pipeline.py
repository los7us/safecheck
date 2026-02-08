"""
Ingestion Pipeline

Orchestrates the full content ingestion flow:
1. Adapter extracts content → CanonicalPost
2. Media processor downloads and extracts features
3. Features attached to CanonicalPost
4. Ready for Gemini analysis
"""

from typing import Optional
from pathlib import Path

from src.core.schemas import CanonicalPost, PlatformName
from src.adapters.registry import adapter_registry
from src.services.media_processor import MediaProcessor


class IngestionPipeline:
    """Orchestrates content ingestion and enrichment"""
    
    def __init__(self, media_cache_dir: Path):
        """
        Initialize ingestion pipeline.
        
        Args:
            media_cache_dir: Directory for media cache
        """
        self.media_processor = MediaProcessor(media_cache_dir)
    
    async def ingest_from_url(self, url: str) -> CanonicalPost:
        """
        Ingest content from a URL.
        
        Full pipeline:
        1. Find appropriate adapter
        2. Extract content
        3. Download and process media
        4. Attach media features
        
        Args:
            url: Platform-specific URL
        
        Returns:
            Enriched CanonicalPost
        
        Raises:
            ValueError: If no adapter can handle URL
        """
        # Find adapter
        adapter = adapter_registry.get_adapter_for_url(url)
        if not adapter:
            raise ValueError(f"No adapter found for URL: {url}")
        
        # Extract content
        post = await adapter.extract(url)
        
        # Process media (if present)
        if post.media_items and len(post.media_items) > 0:
            media_features = await self.media_processor.process_media_list(
                post.media_items
            )
            post.media_features = media_features
        
        return post
    
    async def ingest_from_text(
        self, 
        raw_text: str, 
        platform_hint: Optional[PlatformName] = None
    ) -> CanonicalPost:
        """
        Ingest content from pasted text.
        
        Args:
            raw_text: Pasted content
            platform_hint: Optional platform name hint
        
        Returns:
            CanonicalPost (minimal, no media)
        """
        # For paste mode, use first available adapter or hint
        adapter = None
        
        if platform_hint:
            adapter = adapter_registry.get_adapter(platform_hint)
        
        if not adapter:
            # Fallback to first available adapter
            platforms = adapter_registry.list_platforms()

            if platforms:
                adapter = adapter_registry.get_adapter(platforms[0])
        
        if not adapter:
            raise ValueError("No adapters registered")
        
        return await adapter.extract_from_text(raw_text)
    
    async def cleanup(self):
        """Clean up resources"""
        await self.media_processor.cleanup()
