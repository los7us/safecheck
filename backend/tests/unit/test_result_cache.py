"""Tests for result cache"""

import pytest
from datetime import datetime

from src.cache.result_cache import ResultCache
from src.core.schemas import SafetyAnalysisResult, RiskLevel


@pytest.fixture
def sample_result():
    return SafetyAnalysisResult(
        risk_score=0.75,
        risk_level=RiskLevel.HIGH,
        summary="Test summary",
        key_signals=["Signal 1", "Signal 2"],
        fact_checks=[],
        analysis_timestamp=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_memory_cache_basic(sample_result):
    """Test basic cache operations"""
    cache = ResultCache(backend="memory")
    
    key = cache.generate_cache_key(url="https://example.com/test")
    
    # Cache miss
    result = await cache.get(key)
    assert result is None
    
    # Set value
    await cache.set(key, sample_result)
    
    # Cache hit
    result = await cache.get(key)
    assert result is not None
    assert result.risk_score == 0.75
    assert result.risk_level == RiskLevel.HIGH
    
    # Delete
    await cache.delete(key)
    result = await cache.get(key)
    assert result is None


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation"""
    cache = ResultCache(backend="memory")
    
    key1 = cache.generate_cache_key(url="https://example.com/test")
    key2 = cache.generate_cache_key(url="https://example.com/test")
    assert key1 == key2
    
    key3 = cache.generate_cache_key(url="https://example.com/other")
    assert key1 != key3
    
    key4 = cache.generate_cache_key(text="https://example.com/test")
    assert key1 != key4


@pytest.mark.asyncio
async def test_cache_clear(sample_result):
    """Test cache clear"""
    cache = ResultCache(backend="memory")
    
    key1 = cache.generate_cache_key(url="https://example.com/1")
    key2 = cache.generate_cache_key(url="https://example.com/2")
    
    await cache.set(key1, sample_result)
    await cache.set(key2, sample_result)
    
    await cache.clear()
    
    assert await cache.get(key1) is None
    assert await cache.get(key2) is None
