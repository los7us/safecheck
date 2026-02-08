"""
Media Cache Manager

Handles downloading and caching of media files using content-based hashing.

Design:
- Hash-based storage (deduplication automatic)
- Directory sharding (first 2 chars of hash)
- Size limits enforced
- Automatic cache cleanup (optional)

Cache Structure:
media_cache/
  ab/
    ab1234567890.jpg
  cd/
    cd1122334455.png
"""

import hashlib
import aiofiles
import httpx
from pathlib import Path
from typing import Optional, Tuple


class MediaCacheException(Exception):
    """Base exception for media cache errors"""
    pass


class MediaCache:
    """
    Content-addressed media cache.
    
    Uses SHA-256 hashing for deduplication.
    """
    
    def __init__(self, cache_dir: Path, max_size_mb: int = 10):
        """
        Initialize media cache.
        
        Args:
            cache_dir: Root directory for cache
            max_size_mb: Maximum file size to cache (MB)
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # HTTP client for downloads
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "SafetyCheck/1.0 MediaBot"
            }
        )
    
    async def download_and_cache(
        self, 
        url: str,
        expected_hash: Optional[str] = None
    ) -> Tuple[Path, str]:
        """
        Download media and cache it.
        
        Args:
            url: URL of media to download
            expected_hash: Optional expected content hash for validation
        
        Returns:
            Tuple of (cache_file_path, content_hash)
        
        Raises:
            MediaCacheException: If download or caching fails
        """
        try:
            # Download content
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            content = response.content
            
            # Check size
            if len(content) > self.max_size_bytes:
                raise MediaCacheException(
                    f"File too large: {len(content)} bytes (max: {self.max_size_bytes})"
                )
            
            # Compute hash
            content_hash = hashlib.sha256(content).hexdigest()
            
            # Validate hash if provided
            if expected_hash and content_hash != expected_hash:
                raise MediaCacheException(
                    f"Hash mismatch. Expected: {expected_hash}, Got: {content_hash}"
                )
            
            # Check if already cached
            cache_path = self.get_cache_path(content_hash, url)
            if cache_path.exists():
                return cache_path, content_hash
            
            # Cache the file
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(content)
            
            return cache_path, content_hash
        
        except httpx.HTTPStatusError as e:
            raise MediaCacheException(f"HTTP error downloading {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            raise MediaCacheException(f"Request error downloading {url}: {e}")
        except MediaCacheException:
            raise
        except Exception as e:
            raise MediaCacheException(f"Failed to download and cache {url}: {e}")
    
    def get_cache_path(self, content_hash: str, url: str) -> Path:
        """
        Get cache file path for a given content hash.
        
        Uses directory sharding (first 2 chars) and preserves file extension.
        
        Args:
            content_hash: SHA-256 hash of content
            url: Original URL (for extension detection)
        
        Returns:
            Path to cache file
        """
        # Extract extension from URL
        extension = self._get_extension(url)
        
        # Shard directory (first 2 chars)
        shard = content_hash[:2]
        
        # Full filename
        filename = f"{content_hash}{extension}"
        
        return self.cache_dir / shard / filename
    
    def _get_extension(self, url: str) -> str:
        """Extract file extension from URL"""
        # Try to get extension from URL
        path = url.split('?')[0]  # Remove query params
        ext = Path(path).suffix
        
        if ext and len(ext) <= 5:  # Reasonable extension length
            return ext.lower()
        
        # Default to .bin if no extension
        return '.bin'
    
    def is_cached(self, content_hash: str, url: str = "") -> bool:
        """
        Check if content is already cached.
        
        Args:
            content_hash: SHA-256 hash of content
            url: Optional URL for extension detection
        
        Returns:
            True if cached
        """
        cache_path = self.get_cache_path(content_hash, url)
        return cache_path.exists()
    
    async def get_cached_file(self, content_hash: str, url: str = "") -> Optional[Path]:
        """
        Get path to cached file if it exists.
        
        Args:
            content_hash: Content hash
            url: Optional URL for extension detection
        
        Returns:
            Path if cached, None otherwise
        """
        cache_path = self.get_cache_path(content_hash, url)
        if cache_path.exists():
            return cache_path
        return None
    
    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with file count and total size
        """
        total_files = 0
        total_size = 0
        
        for file_path in self.cache_dir.rglob('*'):
            if file_path.is_file():
                total_files += 1
                total_size += file_path.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
        }
    
    async def cleanup_old_files(self, max_age_days: int = 7) -> int:
        """
        Remove cached files older than max_age_days.
        
        Args:
            max_age_days: Maximum age in days
        
        Returns:
            Number of files removed
        """
        import time
        
        now = time.time()
        max_age_seconds = max_age_days * 86400
        
        removed_count = 0
        for file_path in self.cache_dir.rglob('*'):
            if file_path.is_file():
                age = now - file_path.stat().st_mtime
                if age > max_age_seconds:
                    file_path.unlink()
                    removed_count += 1
        
        return removed_count
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()
