"""
Result Cache

Caches SafetyAnalysisResult to avoid redundant Gemini API calls.
Supports multiple backends: in-memory, Redis.
"""

from typing import Optional, Dict
from datetime import datetime, timedelta
import hashlib
import pickle

from src.core.schemas import SafetyAnalysisResult


class CacheBackend:
    """Base class for cache backends"""
    
    async def get(self, key: str) -> Optional[SafetyAnalysisResult]:
        raise NotImplementedError
    
    async def set(
        self,
        key: str,
        value: SafetyAnalysisResult,
        ttl_seconds: int = 3600
    ) -> None:
        raise NotImplementedError
    
    async def delete(self, key: str) -> None:
        raise NotImplementedError
    
    async def clear(self) -> None:
        raise NotImplementedError
    
    async def close(self) -> None:
        """Cleanup on shutdown"""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend (for MVP/development)"""
    
    def __init__(self):
        self.cache: Dict[str, tuple[SafetyAnalysisResult, datetime]] = {}
    
    async def get(self, key: str) -> Optional[SafetyAnalysisResult]:
        if key in self.cache:
            result, expiry = self.cache[key]
            
            if datetime.utcnow() < expiry:
                return result
            else:
                del self.cache[key]
        
        return None
    
    async def set(
        self,
        key: str,
        value: SafetyAnalysisResult,
        ttl_seconds: int = 3600
    ) -> None:
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self.cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]
    
    async def clear(self) -> None:
        self.cache.clear()
    
    def get_size(self) -> int:
        return len(self.cache)


class RedisCacheBackend(CacheBackend):
    """Redis cache backend (for production)"""
    
    def __init__(self, redis_url: str):
        try:
            import redis.asyncio as redis_async
            self.redis = redis_async.from_url(redis_url, decode_responses=False)
        except ImportError:
            raise ImportError("redis package required. Install: pip install redis")
    
    async def get(self, key: str) -> Optional[SafetyAnalysisResult]:
        data = await self.redis.get(key)
        if data:
            try:
                result_dict = pickle.loads(data)
                return SafetyAnalysisResult(**result_dict)
            except Exception as e:
                print(f"Failed to deserialize: {e}")
                return None
        return None
    
    async def set(
        self,
        key: str,
        value: SafetyAnalysisResult,
        ttl_seconds: int = 3600
    ) -> None:
        data = pickle.dumps(value.model_dump())
        await self.redis.setex(key, ttl_seconds, data)
    
    async def delete(self, key: str) -> None:
        await self.redis.delete(key)
    
    async def clear(self) -> None:
        await self.redis.flushdb()
    
    async def close(self) -> None:
        await self.redis.close()


class ResultCache:
    """
    High-level cache interface for SafetyAnalysisResult.
    """
    
    def __init__(
        self,
        backend: str = "memory",
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,
    ):
        self.default_ttl = default_ttl
        
        if backend == "memory":
            self._backend = MemoryCacheBackend()
        elif backend == "redis":
            if not redis_url:
                raise ValueError("redis_url required for Redis backend")
            self._backend = RedisCacheBackend(redis_url)
        else:
            raise ValueError(f"Unknown cache backend: {backend}")
    
    def generate_cache_key(
        self,
        url: Optional[str] = None,
        text: Optional[str] = None,
    ) -> str:
        """Generate cache key from URL or text."""
        if url:
            content = f"url:{url}"
        elif text:
            content = f"text:{text}"
        else:
            raise ValueError("Either url or text must be provided")
        
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return f"analysis:{hash_obj.hexdigest()}"
    
    async def get(self, key: str) -> Optional[SafetyAnalysisResult]:
        return await self._backend.get(key)
    
    async def set(
        self,
        key: str,
        result: SafetyAnalysisResult,
        ttl: Optional[int] = None,
    ) -> None:
        ttl = ttl or self.default_ttl
        await self._backend.set(key, result, ttl)
    
    async def delete(self, key: str) -> None:
        await self._backend.delete(key)
    
    async def clear(self) -> None:
        await self._backend.clear()
    
    async def close(self) -> None:
        await self._backend.close()
