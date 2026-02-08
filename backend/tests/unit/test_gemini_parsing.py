"""Tests for Gemini response parsing"""

import pytest
import json

from src.services.gemini_service import GeminiService
from src.core.schemas import RiskLevel, ClaimVerdict


@pytest.fixture
def gemini_service():
    return GeminiService(api_key="test_key")


class TestValidResponseParsing:
    """Test parsing valid responses"""
    
    def test_parse_valid_response(self, gemini_service):
        """Test parsing a valid response"""
        response = json.dumps({
            "risk_score": 0.75,
            "risk_level": "High",
            "summary": "This appears to be a scam",
            "key_signals": [
                "Unrealistic promises",
                "Urgency tactics",
                "New account"
            ],
            "fact_checks": []
        })
        
        result = gemini_service._parse_response(response)
        
        assert result.risk_score == 0.75
        assert result.risk_level == RiskLevel.HIGH
        assert len(result.key_signals) == 3
        assert len(result.fact_checks) == 0
    
    def test_parse_response_with_fact_checks(self, gemini_service):
        """Test parsing response with fact-checks"""
        response = json.dumps({
            "risk_score": 0.85,
            "risk_level": "High",
            "summary": "Contains false claims",
            "key_signals": ["False claims", "Misleading"],
            "fact_checks": [
                {
                    "claim": "Guaranteed 10x returns",
                    "verdict": "False",
                    "explanation": "No investment can guarantee returns",
                    "citations": [
                        {
                            "source_name": "U.S. SEC",
                            "url": "https://www.sec.gov/investor/alerts",
                            "excerpt": "Guaranteed returns are red flags"
                        }
                    ]
                }
            ]
        })
        
        result = gemini_service._parse_response(response)
        
        assert len(result.fact_checks) == 1
        assert result.fact_checks[0].claim == "Guaranteed 10x returns"
        assert result.fact_checks[0].verdict == ClaimVerdict.FALSE
        assert len(result.fact_checks[0].citations) == 1
    
    def test_parse_response_with_markdown(self, gemini_service):
        """Test parsing response wrapped in markdown code blocks"""
        response = """```json
        {
            "risk_score": 0.5,
            "risk_level": "Moderate",
            "summary": "Test",
            "key_signals": ["Signal 1", "Signal 2"],
            "fact_checks": []
        }
        ```"""
        
        result = gemini_service._parse_response(response)
        
        assert result.risk_score == 0.5
        assert result.risk_level == RiskLevel.MODERATE


class TestInvalidResponseHandling:
    """Test handling of invalid responses"""
    
    def test_parse_invalid_json(self, gemini_service):
        """Test parsing invalid JSON raises error"""
        response = "This is not JSON"
        
        with pytest.raises(json.JSONDecodeError):
            gemini_service._parse_response(response)
    
    def test_parse_missing_required_field(self, gemini_service):
        """Test parsing with missing required field"""
        response = json.dumps({
            "risk_score": 0.5,
            # Missing risk_level
            "summary": "Test",
            "key_signals": ["Signal"],
        })
        
        with pytest.raises((ValueError, KeyError)):
            gemini_service._parse_response(response)


class TestErrorHandler:
    """Test error handler"""
    
    def test_create_fallback_result(self):
        """Test fallback result creation"""
        from src.services.gemini_error_handler import GeminiErrorHandler
        
        result = GeminiErrorHandler.create_fallback_result("Test reason")
        
        assert result.risk_score == 0.5
        assert result.risk_level == RiskLevel.MODERATE
        assert "Test reason" in result.summary
        assert result.model_version == "fallback"
    
    def test_is_retryable_error_rate_limit(self):
        """Test rate limit error is retryable"""
        from src.services.gemini_error_handler import GeminiErrorHandler
        
        error = Exception("Rate limit exceeded")
        assert GeminiErrorHandler.is_retryable_error(error) is True
    
    def test_is_retryable_error_normal(self):
        """Test normal error is not retryable"""
        from src.services.gemini_error_handler import GeminiErrorHandler
        
        error = Exception("Invalid API key")
        assert GeminiErrorHandler.is_retryable_error(error) is False
