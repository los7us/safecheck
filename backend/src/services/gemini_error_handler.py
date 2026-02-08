"""
Gemini Error Handler

Handles various error scenarios:
- API rate limits
- Malformed responses
- Blocked content
- Network errors
"""

from datetime import datetime
from src.core.schemas import SafetyAnalysisResult, RiskLevel


class GeminiErrorHandler:
    """Handle Gemini API errors gracefully"""
    
    @staticmethod
    def create_fallback_result(
        reason: str = "Analysis unavailable"
    ) -> SafetyAnalysisResult:
        """
        Create a fallback result when analysis fails.
        
        This ensures the system never crashes, even if Gemini fails.
        
        Args:
            reason: Reason for fallback
        
        Returns:
            Safe fallback SafetyAnalysisResult
        """
        return SafetyAnalysisResult(
            risk_score=0.5,  # Neutral score
            risk_level=RiskLevel.MODERATE,
            summary=f"Unable to complete analysis: {reason}. Please review manually.",
            key_signals=[
                "Automated analysis unavailable",
                "Manual review recommended",
            ],
            fact_checks=[],
            analysis_timestamp=datetime.utcnow(),
            model_version="fallback",
        )
    
    @staticmethod
    def is_retryable_error(error: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            error: The exception that occurred
        
        Returns:
            True if error is retryable (rate limit, timeout, etc.)
        """
        error_str = str(error).lower()
        
        retryable_keywords = [
            "rate limit",
            "timeout",
            "503",
            "429",
            "temporarily unavailable",
            "overloaded",
            "resource exhausted",
        ]
        
        return any(keyword in error_str for keyword in retryable_keywords)
    
    @staticmethod
    def get_error_category(error: Exception) -> str:
        """
        Categorize an error for logging/metrics.
        
        Args:
            error: The exception
        
        Returns:
            Category string
        """
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "429" in error_str:
            return "rate_limit"
        elif "timeout" in error_str:
            return "timeout"
        elif "blocked" in error_str:
            return "content_blocked"
        elif "invalid" in error_str and "key" in error_str:
            return "auth_error"
        elif "json" in error_str or "parse" in error_str:
            return "parse_error"
        else:
            return "unknown"
