"""
Integration tests for media pipeline.

Tests the full flow:
1. Media processor downloads and caches
2. Features extracted
3. Features attached to CanonicalPost
"""

import pytest
import os
from pathlib import Path
import tempfile
import shutil

from src.services.media_processor import MediaProcessor
from src.core.schemas import MediaType, MediaMetadata


@pytest.fixture
def temp_cache():
    """Create temporary cache directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def media_processor(temp_cache):
    """Create MediaProcessor instance"""
    return MediaProcessor(temp_cache)


SKIP_INTEGRATION = os.getenv('SKIP_INTEGRATION_TESTS', '0') == '1'


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests skipped")
@pytest.mark.asyncio
async def test_process_image_from_url(media_processor):
    """Test processing a real image URL"""
    # Use a stable public image
    test_url = "https://via.placeholder.com/300x200.png"
    
    metadata, features = await media_processor.process_media(
        test_url,
        MediaType.IMAGE
    )
    
    # Verify metadata
    assert metadata.media_type == MediaType.IMAGE
    assert metadata.url == test_url
    assert metadata.hash is not None
    assert metadata.width == 300
    assert metadata.height == 200
    
    # Verify features
    assert features is not None
    assert features.caption is not None
    
    print(f"✓ Processed image: {metadata.hash}")
    print(f"  Caption: {features.caption}")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests skipped")
@pytest.mark.asyncio
async def test_cache_deduplication(media_processor):
    """Test that same image is cached and reused"""
    test_url = "https://via.placeholder.com/150.png"
    
    # First download
    metadata1, _ = await media_processor.process_media(test_url, MediaType.IMAGE)
    
    # Second download (should hit cache)
    metadata2, _ = await media_processor.process_media(test_url, MediaType.IMAGE)
    
    # Same hash means same file
    assert metadata1.hash == metadata2.hash
    
    print("✓ Cache deduplication works")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests skipped")
@pytest.mark.asyncio
async def test_process_media_list(media_processor):
    """Test processing list of media items"""
    media_items = [
        MediaMetadata(
            media_type=MediaType.IMAGE,
            url="https://via.placeholder.com/100.png",
        ),
    ]
    
    features = await media_processor.process_media_list(media_items)
    
    # Should process first image
    assert features is not None
    assert features.caption is not None
    
    print("✓ Media list processing works")


@pytest.mark.asyncio
async def test_empty_media_list(media_processor):
    """Test processing empty media list"""
    features = await media_processor.process_media_list([])
    assert features is None


@pytest.mark.asyncio
async def test_metrics(media_processor):
    """Test metrics tracking"""
    metrics = media_processor.get_metrics()
    assert 'total_processed' in metrics
    assert 'cache_stats' in metrics
