"""
Pytest fixtures for backend tests.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from src.core.schemas import (
    SafetyAnalysisResult, RiskLevel, CanonicalPost,
    PlatformName, FactCheck, Citation, ClaimVerdict
)


@pytest.fixture
def sample_result():
    """Create sample analysis result"""
    return SafetyAnalysisResult(
        risk_score=0.75,
        risk_level=RiskLevel.HIGH,
        summary="This appears to be a scam",
        key_signals=["Unrealistic promises", "Urgency tactics"],
        fact_checks=[
            FactCheck(
                claim="Guaranteed 10x returns",
                verdict=ClaimVerdict.FALSE,
                explanation="No legitimate investments guarantee returns",
                citations=[
                    Citation(
                        source_name="SEC.gov",
                        url="https://www.sec.gov/example",
                        excerpt="Investment fraud warning signs"
                    )
                ]
            )
        ],
        analysis_timestamp=datetime.utcnow(),
        model_version="gemini-1.5-pro"
    )


@pytest.fixture
def sample_post():
    """Create sample canonical post"""
    return CanonicalPost(
        post_id="test123",
        post_text="URGENT! Invest now for guaranteed returns!",
        platform_name=PlatformName.REDDIT,
    )


@pytest.fixture
def mock_gemini_service(sample_result):
    """Create mock Gemini service"""
    mock = Mock()
    mock.analyze = AsyncMock(return_value=sample_result)
    mock.get_metrics = Mock(return_value={
        "total_requests": 10,
        "total_tokens": 5000,
        "avg_latency": 2.5,
    })
    return mock


@pytest.fixture
def mock_pipeline(sample_post):
    """Create mock ingestion pipeline"""
    mock = Mock()
    mock.ingest_from_url = AsyncMock(return_value=sample_post)
    mock.ingest_from_text = AsyncMock(return_value=sample_post)
    mock.cleanup = AsyncMock()
    return mock


@pytest.fixture
def mock_cache(sample_result):
    """Create mock result cache"""
    mock = Mock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.clear = AsyncMock()
    mock.close = AsyncMock()
    mock.generate_cache_key = Mock(return_value="test_cache_key")
    return mock


@pytest.fixture
def mock_metrics():
    """Create mock metrics tracker"""
    mock = Mock()
    mock.check_rate_limit = Mock(return_value=True)
    mock.record_request = Mock()
    mock.record_cache_hit = Mock()
    mock.record_cache_miss = Mock()
    mock.get_cache_stats = Mock(return_value={
        "total_hits": 10,
        "total_misses": 5,
        "hit_rate": 0.67,
    })
    mock.get_request_stats = Mock(return_value={
        "total_requests": 15,
        "avg_latency_seconds": 2.5,
        "total_tokens": 5000,
    })
    mock.get_rate_limit_stats = Mock(return_value={
        "hourly": {"count": 10, "limit": 100, "remaining": 90},
        "daily": {"requests": {"count": 15, "limit": 1000, "remaining": 985}},
    })
    return mock
