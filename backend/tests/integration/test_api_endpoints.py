"""
Integration tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock

# Import app for testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def client():
    """Create test client with mocked dependencies"""
    with patch('src.main.pipeline') as mock_pipeline, \
         patch('src.main.gemini_service') as mock_gemini, \
         patch('src.main.result_cache') as mock_cache, \
         patch('src.main.metrics') as mock_metrics:
        
        from src.main import app
        yield TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    with patch('src.main.pipeline'), \
         patch('src.main.gemini_service'), \
         patch('src.main.result_cache'), \
         patch('src.main.metrics'):
        from src.main import app
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "SafetyCheck API"
        assert data["status"] == "online"


def test_health_endpoint():
    """Test health check endpoint"""
    with patch('src.main.pipeline', Mock()), \
         patch('src.main.gemini_service', Mock()), \
         patch('src.main.result_cache', Mock()), \
         patch('src.main.metrics', Mock()):
        from src.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


def test_analyze_missing_input():
    """Test analyze with missing input"""
    with patch('src.main.pipeline'), \
         patch('src.main.gemini_service'), \
         patch('src.main.result_cache') as mock_cache, \
         patch('src.main.metrics'):
        
        mock_cache.generate_cache_key = Mock(side_effect=ValueError("Either url or text"))
        
        from src.main import app
        client = TestClient(app)
        
        response = client.post("/api/analyze", json={})
        
        assert response.status_code == 400


def test_analyze_rate_limit():
    """Test rate limit enforcement"""
    with patch('src.main.pipeline'), \
         patch('src.main.gemini_service'), \
         patch('src.main.result_cache') as mock_cache, \
         patch('src.main.metrics') as mock_metrics:
        
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.generate_cache_key = Mock(return_value="key")
        mock_metrics.check_rate_limit = Mock(return_value=False)
        mock_metrics.record_cache_miss = Mock()
        
        from src.main import app
        client = TestClient(app)
        
        response = client.post("/api/analyze", json={"text": "test"})
        
        assert response.status_code == 429


def test_metrics_endpoint():
    """Test metrics endpoint"""
    with patch('src.main.pipeline'), \
         patch('src.main.gemini_service') as mock_gemini, \
         patch('src.main.result_cache'), \
         patch('src.main.metrics') as mock_metrics:
        
        mock_metrics.get_cache_stats = Mock(return_value={"hit_rate": 0.67})
        mock_metrics.get_request_stats = Mock(return_value={"total_requests": 15})
        mock_metrics.get_rate_limit_stats = Mock(return_value={"hourly": {}})
        mock_gemini.get_metrics = Mock(return_value={"model": "gemini-1.5-pro"})
        
        from src.main import app
        client = TestClient(app)
        
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "cache" in data
        assert "requests" in data


def test_clear_cache():
    """Test cache clearing"""
    with patch('src.main.pipeline'), \
         patch('src.main.gemini_service'), \
         patch('src.main.result_cache') as mock_cache, \
         patch('src.main.metrics'):
        
        mock_cache.clear = AsyncMock()
        
        from src.main import app
        client = TestClient(app)
        
        response = client.delete("/api/cache")
        
        assert response.status_code == 200
        assert "cleared" in response.json()["message"].lower()
