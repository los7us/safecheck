"""Unit tests for media cache"""

import pytest
from pathlib import Path
import tempfile
import shutil

from src.utils.media_cache import MediaCache, MediaCacheException


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def media_cache(temp_cache_dir):
    """Create MediaCache instance"""
    return MediaCache(temp_cache_dir, max_size_mb=5)


class TestMediaCacheInitialization:
    """Test cache initialization"""
    
    def test_cache_directory_created(self, media_cache, temp_cache_dir):
        """Test cache directory is created"""
        assert temp_cache_dir.exists()
        assert media_cache.cache_dir == temp_cache_dir
    
    def test_max_size_set(self, media_cache):
        """Test max size is set correctly"""
        assert media_cache.max_size_bytes == 5 * 1024 * 1024


class TestCachePathGeneration:
    """Test cache path generation"""
    
    def test_get_cache_path(self, media_cache):
        """Test cache path generation"""
        content_hash = "abcdef1234567890" * 4  # 64 chars
        url = "https://example.com/image.jpg"
        
        path = media_cache.get_cache_path(content_hash, url)
        
        # Should be in shard directory (first 2 chars)
        assert path.parent.name == "ab"
        assert path.name.startswith(content_hash)
        assert path.suffix == ".jpg"
    
    def test_cache_path_with_png(self, media_cache):
        """Test cache path with PNG extension"""
        content_hash = "cd" + "0" * 62
        url = "https://example.com/photo.png"
        
        path = media_cache.get_cache_path(content_hash, url)
        assert path.suffix == ".png"
    
    def test_cache_path_with_query_params(self, media_cache):
        """Test extension extraction with query params"""
        content_hash = "ef" + "0" * 62
        url = "https://example.com/image.jpg?size=large&quality=high"
        
        path = media_cache.get_cache_path(content_hash, url)
        assert path.suffix == ".jpg"


class TestExtensionExtraction:
    """Test file extension extraction"""
    
    def test_jpg_extension(self, media_cache):
        """Test JPG extension extraction"""
        assert media_cache._get_extension("https://example.com/image.jpg") == ".jpg"
    
    def test_png_extension(self, media_cache):
        """Test PNG extension extraction"""
        assert media_cache._get_extension("https://example.com/photo.png") == ".png"
    
    def test_extension_with_query(self, media_cache):
        """Test extension with query params"""
        assert media_cache._get_extension("https://example.com/img.gif?s=100") == ".gif"
    
    def test_no_extension(self, media_cache):
        """Test fallback when no extension"""
        assert media_cache._get_extension("https://example.com/file") == ".bin"


class TestCacheStats:
    """Test cache statistics"""
    
    def test_empty_cache_stats(self, media_cache):
        """Test cache stats for empty cache"""
        stats = media_cache.get_cache_stats()
        assert stats['total_files'] == 0
        assert stats['total_size_mb'] == 0
    
    def test_cache_dir_in_stats(self, media_cache, temp_cache_dir):
        """Test cache dir is in stats"""
        stats = media_cache.get_cache_stats()
        assert str(temp_cache_dir) == stats['cache_dir']


class TestIsCached:
    """Test is_cached functionality"""
    
    def test_not_cached(self, media_cache):
        """Test file not cached"""
        fake_hash = "a" * 64
        assert not media_cache.is_cached(fake_hash, "https://example.com/test.jpg")
