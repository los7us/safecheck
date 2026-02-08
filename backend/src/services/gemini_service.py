"""
Gemini AI Service

Handles all interactions with Google's Gemini API.

Responsibilities:
- Format prompts from CanonicalPost
- Call Gemini API
- Parse and validate responses
- Retry on malformed output
- Track token usage and latency
"""

from typing import Optional
import json
import time
from datetime import datetime
from src.core.schemas import (
    CanonicalPost,
    SafetyAnalysisResult,
    RiskLevel,
    FactCheck,
    Citation,
    ClaimVerdict,
)
from src.services.gemini_prompts import (
    build_analysis_prompt,
    build_author_context,
    build_engagement_context,
    build_media_summary,
)
import google.generativeai as genai


class GeminiServiceException(Exception):
    """Base exception for Gemini service errors"""
    pass


class GeminiParseError(GeminiServiceException):
    """Raised when Gemini response cannot be parsed"""
    pass


class GeminiAPIError(GeminiServiceException):
    """Raised when Gemini API call fails"""
    pass


class GeminiRateLimitError(GeminiServiceException):
    """Raised when Gemini API rate limit exceeded"""
    pass


class GeminiService:
    """Service for interacting with Gemini API"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key
            model_name: Model to use
        """
        genai.configure(api_key=api_key)
        self.model_name = model_name
        
        # Configure generation parameters
        generation_config = genai.GenerationConfig(
            temperature=0.3,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
        )
        
        # Tracking
        self.total_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
    
    async def analyze(self, canonical_post: CanonicalPost, max_retries: int = 2) -> SafetyAnalysisResult:
        """
        Analyze a post for safety risks.
        
        Args:
            canonical_post: Normalized post data
            max_retries: Maximum retry attempts for malformed responses
        
        Returns:
            SafetyAnalysisResult
        
        Raises:
            GeminiServiceException: If analysis fails
        """
        # Build prompt
        prompt = self._build_prompt_from_post(canonical_post)
        
        # Call Gemini with retries
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = await self._call_gemini(prompt)
                latency = time.time() - start_time
                
                # Parse and validate
                result = self._parse_response(response)
                
                # Track metrics
                self._update_metrics(latency, response)
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries:
                    # Retry with same prompt, model might fix itself
                    continue
                raise GeminiParseError(f"Failed to parse Gemini response after {max_retries} retries: {e}")
        
        raise GeminiServiceException("Unexpected retry loop exit")
    
    def _build_prompt_from_post(self, post: CanonicalPost) -> str:
        """Convert CanonicalPost to analysis prompt"""
        # Build context strings
        author_context = None
        if post.author_metadata:
            am = post.author_metadata
            author_context = build_author_context(
                am.author_type.value,
                am.account_age_bucket.value,
                am.is_verified,
                am.follower_count_bucket
            )
        
        engagement_context = None
        if post.engagement_metrics:
            em = post.engagement_metrics
            engagement_context = build_engagement_context(
                em.likes, em.shares, em.replies, em.views
            )
        
        media_summary = None
        if post.media_features:
            mf = post.media_features
            media_summary = build_media_summary(
                mf.caption, mf.ocr_text, mf.detected_objects
            )
        
        return build_analysis_prompt(
            post_text=post.post_text,
            platform_name=post.platform_name.value,
            media_summary=media_summary,
            author_context=author_context,
            engagement_context=engagement_context,
            external_links=post.external_links if post.external_links else None,
        )
    
    async def _call_gemini(self, prompt: str) -> str:
        """Make actual API call to Gemini"""
        try:
            # Generate content
            response = await self.model.generate_content_async(prompt)
            
            # Check for block reasons
            if response.prompt_feedback.block_reason:
                raise GeminiServiceException(f"Prompt blocked: {response.prompt_feedback.block_reason}")
                
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                raise GeminiRateLimitError(f"Gemini API rate limit exceeded: {error_msg}")
            raise GeminiAPIError(f"Gemini API call failed: {e}")
    
    def _parse_response(self, response_text: str) -> SafetyAnalysisResult:
        """Parse and validate Gemini response"""
        # Clean up response (remove markdown code blocks if present)
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        # Parse JSON
        print(f"DEBUG: Gemini raw response: {text}")
        data = json.loads(text)
        
        # Build fact checks
        fact_checks = []
        for fc_data in data.get("fact_checks", []):
            citations = [
                Citation(
                    source_name=c["source_name"],
                    url=c["url"],
                    excerpt=c.get("excerpt")
                )
                for c in fc_data.get("citations", [])
            ]
            try:
                fact_checks.append(FactCheck(
                    claim=fc_data.get("claim", fc_data.get("claim_text", "Unknown Claim")), # Fallback to claim_text
                    verdict=ClaimVerdict(fc_data["verdict"]),
                    explanation=fc_data["explanation"],
                    citations=citations
                ))
            except KeyError as e:
                print(f"ERROR: Missing key in fact check data: {e}. Data: {fc_data}")
                continue # Skip malformed fact check
        
        # Build result
        return SafetyAnalysisResult(
            risk_score=float(data["risk_score"]),
            risk_level=RiskLevel(data["risk_level"]),
            summary=data["summary"],
            key_signals=data["key_signals"],
            fact_checks=fact_checks,
            analysis_timestamp=datetime.utcnow(),
            model_version=self.model_name
        )
    
    def _update_metrics(self, latency: float, response: str) -> None:
        """Update service metrics"""
        self.total_requests += 1
        self.total_latency += latency
        # Token counting approximation (actual would use API response metadata)
        self.total_tokens += len(response) // 4
    
    def get_metrics(self) -> dict:
        """Return service metrics"""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "avg_latency": self.total_latency / max(self.total_requests, 1),
        }
