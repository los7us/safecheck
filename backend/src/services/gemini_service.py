"""
Gemini AI Service (VISION-ENABLED)

Handles all interactions with Google's Gemini API.
Supports both text-only and multimodal (text + image) analysis.

Uses the google.genai SDK (migrated from deprecated google.generativeai).

Responsibilities:
- Format prompts from CanonicalPost
- Call Gemini API (text or vision mode)
- Resize images for optimal API usage
- Parse and validate responses
- Retry on malformed output
- Track token usage and latency
"""

from typing import Optional
from pathlib import Path
import json
import time
import io
from datetime import datetime

from PIL import Image

from src.core.schemas import (
    CanonicalPost,
    SafetyAnalysisResult,
    RiskLevel,
    FactCheck,
    Citation,
    ClaimVerdict,
    VerificationStatus,
    ConfidenceLabel,
)
from src.services.gemini_prompts import (
    build_analysis_prompt,
    build_vision_analysis_prompt,
    build_author_context,
    build_engagement_context,
    build_media_summary,
)

# New SDK
from google import genai
from google.genai import types


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
    """Service for interacting with Gemini API (text and vision)"""
    
    # Maximum image dimension for vision API (controls cost)
    MAX_IMAGE_DIMENSION = 1024
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key
            model_name: Model to use (must support vision for image analysis)
        """
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
        # Generation config for JSON output
        self.generation_config = types.GenerateContentConfig(
            temperature=0.2,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json",
        )
        
        # Tracking
        self.total_requests = 0
        self.vision_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        
        print(f"GeminiService initialized: model={model_name}")
    
    async def analyze(
        self, 
        canonical_post: CanonicalPost, 
        image_path: Optional[Path] = None,
        max_retries: int = 2
    ) -> SafetyAnalysisResult:
        """
        Analyze a post for safety risks.
        
        Args:
            canonical_post: Normalized post data
            image_path: Optional path to image for vision analysis
            max_retries: Maximum retry attempts for malformed responses
        
        Returns:
            SafetyAnalysisResult
        """
        use_vision = image_path is not None and image_path.exists()
        
        if use_vision:
            return await self._analyze_with_vision(
                canonical_post, image_path, max_retries
            )
        else:
            return await self._analyze_text_only(
                canonical_post, max_retries
            )
    
    async def _analyze_text_only(
        self,
        canonical_post: CanonicalPost,
        max_retries: int
    ) -> SafetyAnalysisResult:
        """Text-only analysis."""
        prompt = self._build_prompt_from_post(canonical_post)
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = await self._call_gemini(prompt)
                latency = time.time() - start_time
                
                result = self._parse_response(response)
                self._update_metrics(latency, response, vision=False)
                
                print(f"Analysis complete in {latency:.1f}s: risk={result.risk_level.value}")
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Parse error attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    continue
                raise GeminiParseError(
                    f"Failed to parse response after {max_retries} retries: {e}"
                )
        
        raise GeminiServiceException("Unexpected retry loop exit")
    
    async def _analyze_with_vision(
        self,
        canonical_post: CanonicalPost,
        image_path: Path,
        max_retries: int
    ) -> SafetyAnalysisResult:
        """Vision-enhanced analysis."""
        prompt = self._build_vision_prompt_from_post(canonical_post)
        image = self._load_and_resize_image(image_path)
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = await self._call_gemini(prompt, image=image)
                latency = time.time() - start_time
                
                result = self._parse_response(response)
                result.model_version = f"{self.model_name}-vision"
                self._update_metrics(latency, response, vision=True)
                
                print(f"Vision analysis complete in {latency:.1f}s: risk={result.risk_level.value}")
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Vision parse error attempt {attempt + 1}: {e}")
                if attempt < max_retries:
                    continue
                raise GeminiParseError(
                    f"Failed to parse vision response after {max_retries} retries: {e}"
                )
        
        raise GeminiServiceException("Unexpected retry loop exit")
    
    def _load_and_resize_image(self, image_path: Path) -> Image.Image:
        """
        Load image, resize if needed, and prepare for Gemini Vision API.
        Resizes to max 1024px on longest side to control API costs.
        """
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if larger than max dimension
            width, height = image.size
            max_dim = max(width, height)
            
            if max_dim > self.MAX_IMAGE_DIMENSION:
                scale = self.MAX_IMAGE_DIMENSION / max_dim
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            return image
            
        except Exception as e:
            raise GeminiServiceException(f"Failed to load image: {e}")
    
    async def _call_gemini(self, prompt: str, image: Optional[Image.Image] = None) -> str:
        """
        Unified API call for both text and vision modes.
        """
        try:
            # Build contents
            contents = [prompt, image] if image else prompt
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=self.generation_config,
            )
            
            # Check for safety blocks
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = str(response.candidates[0].finish_reason)
                if "SAFETY" in finish_reason.upper():
                    raise GeminiServiceException("Content blocked by safety filters")
            
            if not response.text:
                raise GeminiServiceException("Empty response from Gemini")
            
            return response.text
            
        except GeminiServiceException:
            raise
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                raise GeminiRateLimitError(f"Gemini API rate limit exceeded: {error_msg}")
            raise GeminiAPIError(f"Gemini API call failed: {e}")
    
    def _build_prompt_from_post(self, post: CanonicalPost) -> str:
        """Convert CanonicalPost to text-only analysis prompt."""
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
    
    def _build_vision_prompt_from_post(self, post: CanonicalPost) -> str:
        """Convert CanonicalPost to vision analysis prompt."""
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
        
        return build_vision_analysis_prompt(
            post_text=post.post_text,
            platform_name=post.platform_name.value,
            author_context=author_context,
            engagement_context=engagement_context,
            external_links=post.external_links if post.external_links else None,
        )
    
    def _parse_response(self, response_text: str) -> SafetyAnalysisResult:
        """Parse and validate Gemini response."""
        text = response_text.strip()
        # Strip markdown code fences if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        
        # Build fact checks (graceful fallback)
        fact_checks = []
        for fc_data in data.get("fact_checks", []):
            citations = []
            for c in fc_data.get("citations", []):
                try:
                    citations.append(Citation(
                        source_name=c.get("source_name", "Unknown"),
                        url=c.get("url", "https://example.com"),
                        excerpt=c.get("excerpt")
                    ))
                except Exception:
                    continue
            
            if not citations:
                continue
                
            try:
                fact_checks.append(FactCheck(
                    claim=fc_data.get("claim", fc_data.get("claim_text", "Unknown Claim")),
                    verdict=ClaimVerdict(fc_data["verdict"]),
                    explanation=fc_data["explanation"],
                    citations=citations
                ))
            except (KeyError, ValueError) as e:
                print(f"Skipping malformed fact check: {e}")
                continue
        
        # Parse verification status (new field, with fallback)
        verification_status = VerificationStatus.NOT_APPLICABLE
        raw_vs = data.get("verification_status")
        if raw_vs:
            try:
                verification_status = VerificationStatus(raw_vs)
            except ValueError:
                pass
        
        # Parse confidence (new fields, with fallback)
        confidence_score = data.get("confidence_score", 0.5)
        if isinstance(confidence_score, dict):
            confidence_score = confidence_score.get("score", 0.5)
        confidence_score = max(0.0, min(1.0, float(confidence_score)))
        
        confidence_label = ConfidenceLabel.MODERATE
        raw_cl = data.get("confidence_label")
        if isinstance(raw_cl, dict):
            raw_cl = raw_cl.get("label")
        if raw_cl:
            try:
                confidence_label = ConfidenceLabel(raw_cl)
            except ValueError:
                pass
        
        # Parse user guidance
        user_guidance = data.get("user_guidance")
        if isinstance(user_guidance, dict):
            user_guidance = user_guidance.get("text", str(user_guidance))
        if user_guidance and len(user_guidance) > 300:
            user_guidance = user_guidance[:297] + "..."
        
        # Parse risk score - handle nested format
        risk_score = data.get("risk_score", 0.5)
        if isinstance(risk_score, dict):
            risk_score = risk_score.get("value", risk_score.get("score", 0.5))
        risk_score = max(0.0, min(1.0, float(risk_score)))
        
        # Parse risk level - handle nested format
        risk_level_raw = data.get("risk_level", "Moderate")
        if isinstance(risk_level_raw, dict):
            risk_level_raw = risk_level_raw.get("value", risk_level_raw.get("label", "Moderate"))
        
        # Normalize risk level string  
        risk_level_str = str(risk_level_raw).strip().capitalize()
        # Map low/medium/high from agent config to our enum
        level_map = {
            "Low": "Low", "Medium": "Moderate", "Moderate": "Moderate",
            "High": "High", "Minimal": "Minimal", "Critical": "Critical",
        }
        risk_level_str = level_map.get(risk_level_str, "Moderate")
        
        # Parse summary
        summary = data.get("summary", data.get("analysis_summary", "Analysis complete."))
        if isinstance(summary, dict):
            summary = summary.get("text", str(summary))
        
        # Parse key signals
        key_signals = data.get("key_signals", data.get("key_signals_detected", []))
        if isinstance(key_signals, list):
            # Flatten if items are dicts
            key_signals = [
                s.get("signal", str(s)) if isinstance(s, dict) else str(s)
                for s in key_signals
            ]
        if len(key_signals) < 2:
            key_signals = key_signals + ["Content analyzed"] * (2 - len(key_signals))
        key_signals = key_signals[:5]
        
        return SafetyAnalysisResult(
            risk_score=risk_score,
            risk_level=RiskLevel(risk_level_str),
            summary=str(summary)[:500],
            key_signals=key_signals,
            verification_status=verification_status,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            user_guidance=user_guidance,
            fact_checks=fact_checks,
            analysis_timestamp=datetime.utcnow(),
            model_version=self.model_name
        )
    
    def _update_metrics(self, latency: float, response: str, vision: bool = False) -> None:
        """Update service metrics."""
        self.total_requests += 1
        self.total_latency += latency
        
        if vision:
            self.vision_requests += 1
        
        self.total_tokens += len(response) // 4
    
    def get_metrics(self) -> dict:
        """Return service metrics."""
        return {
            "total_requests": self.total_requests,
            "vision_requests": self.vision_requests,
            "text_requests": self.total_requests - self.vision_requests,
            "total_tokens": self.total_tokens,
            "avg_latency": self.total_latency / max(self.total_requests, 1),
            "model": self.model_name,
        }
