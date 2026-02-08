"""Tests for metrics tracker"""

import pytest
from src.monitoring.metrics import MetricsTracker


def test_metrics_basic():
    """Test basic metrics tracking"""
    metrics = MetricsTracker()
    
    metrics.record_request(latency=1.5, tokens=500)
    metrics.record_request(latency=2.0, tokens=600)
    
    stats = metrics.get_request_stats()
    
    assert stats["total_requests"] == 2
    assert stats["total_tokens"] == 1100
    assert stats["avg_latency_seconds"] == 1.75


def test_cache_stats():
    """Test cache statistics"""
    metrics = MetricsTracker()
    
    metrics.record_cache_hit()
    metrics.record_cache_hit()
    metrics.record_cache_miss()
    
    stats = metrics.get_cache_stats()
    
    assert stats["total_hits"] == 2
    assert stats["total_misses"] == 1
    assert stats["hit_rate"] == pytest.approx(2/3)


def test_rate_limiting():
    """Test rate limit enforcement"""
    metrics = MetricsTracker(
        hourly_request_limit=5,
        daily_request_limit=10,
    )
    
    for _ in range(5):
        assert metrics.check_rate_limit() == True
        metrics.record_request(latency=1.0, tokens=100)
    
    assert metrics.check_rate_limit() == False


def test_cost_estimation():
    """Test cost estimation"""
    metrics = MetricsTracker()
    
    cost = metrics.estimate_cost(
        input_tokens=1000,
        output_tokens=500,
        model="gemini-1.5-pro"
    )
    
    expected = (1000 * 0.35 / 1_000_000) + (500 * 1.05 / 1_000_000)
    assert cost == pytest.approx(expected)
