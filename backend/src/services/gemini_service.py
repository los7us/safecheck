"""
Gemini AI Service (VISION-ENABLED)

Handles all interactions with Google's Gemini API.
Supports both text-only and multimodal (text + image) analysis.

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
import base64
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
)
from src.services.gemini_prompts import (
    build_analysis_prompt,
    build_vision_analysis_prompt,
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
    """Service for interacting with Gemini API (text and vision)"""
    
    # Maximum image dimension for vision API (controls cost)
    MAX_IMAGE_DIMENSION = 1024
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key
            model_name: Model to use (must support vision for image analysis)
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
        self.vision_requests = 0
        self.total_tokens = 0
        self.total_latency = 0.0
    
    async def analyze(
        self, 
        canonical_post: CanonicalPost, 
        image_path: Optional[Path] = None,
        max_retries: int = 2
    ) -> SafetyAnalysisResult:
        """
        Analyze a post for safety risks.
        
        Supports vision analysis when image_path is provided.
        
        Args:
            canonical_post: Normalized post data
            image_path: Optional path to image for vision analysis
            max_retries: Maximum retry attempts for malformed responses
        
        Returns:
            SafetyAnalysisResult
        
        Raises:
            GeminiServiceException: If analysis fails
        """
        # Determine if using vision mode
        use_vision = image_path is not None and image_path.exists()
        
        if use_vision:
            return await self._analyze_with_vision(
                canonical_post, 
                image_path, 
                max_retries
            )
        else:
            return await self._analyze_text_only(
                canonical_post, 
                max_retries
            )
    
    async def _analyze_text_only(
        self,
        canonical_post: CanonicalPost,
        max_retries: int
    ) -> SafetyAnalysisResult:
        """Text-only analysis (existing functionality)."""
        prompt = self._build_prompt_from_post(canonical_post)
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = await self._call_gemini_text(prompt)
                latency = time.time() - start_time
                
                result = self._parse_response(response)
                self._update_metrics(latency, response, vision=False)
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
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
        """
        Vision-enhanced analysis.
        
        Sends image directly to Gemini Vision API.
        """
        # Build vision prompt
        prompt = self._build_vision_prompt_from_post(canonical_post)
        
        # Load and resize image
        image_data = self._load_and_resize_image(image_path)
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                response = await self._call_gemini_vision(prompt, image_data)
                latency = time.time() - start_time
                
                result = self._parse_response(response)
                result.model_version = f"{self.model_name}-vision"
                self._update_metrics(latency, response, vision=True)
                
                return result
                
            except (json.JSONDecodeError, ValueError) as e:
                if attempt < max_retries:
                    continue
                raise GeminiParseError(
                    f"Failed to parse vision response after {max_retries} retries: {e}"
                )
        
        raise GeminiServiceException("Unexpected retry loop exit")
    
    def _load_and_resize_image(self, image_path: Path) -> dict:
        """
        Load image, resize if needed, and prepare for Gemini Vision API.
        
        Resizes to max 1024px on longest side to control API costs
        while preserving important visual details.
        
        Returns:
            Dict with PIL Image object for Gemini SDK
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary (remove alpha channel)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparency
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
            
            return {"pil_image": image}
            
        except Exception as e:
            raise GeminiServiceException(f"Failed to load image: {e}")
    
    async def _call_gemini_text(self, prompt: str) -> str:
        """Text-only API call."""
        try:
            response = await self.model.generate_content_async(prompt)
            
            if response.prompt_feedback.block_reason:
                raise GeminiServiceException(
                    f"Prompt blocked: {response.prompt_feedback.block_reason}"
                )
            
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                raise GeminiRateLimitError(f"Gemini API rate limit exceeded: {error_msg}")
            raise GeminiAPIError(f"Gemini API call failed: {e}")
    
    async def _call_gemini_vision(self, prompt: str, image_data: dict) -> str:
        """
        Vision API call.
        
        Sends both text prompt and image to Gemini.
        """
        try:
            # Get PIL image
            pil_image = image_data["pil_image"]
            
            # Generate content with image (Gemini SDK handles the image directly)
            response = await self.model.generate_content_async([prompt, pil_image])
            
            if response.prompt_feedback.block_reason:
                raise GeminiServiceException(
                    f"Prompt blocked: {response.prompt_feedback.block_reason}"
                )
            
            if not response.text:
                raise GeminiServiceException("Empty response from Gemini Vision")
            
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                raise GeminiRateLimitError(f"Gemini Vision rate limit exceeded: {error_msg}")
            raise GeminiAPIError(f"Gemini Vision API call failed: {e}")
    
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
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        print(f"DEBUG: Gemini raw response: {text[:500]}...")
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
                    claim=fc_data.get("claim", fc_data.get("claim_text", "Unknown Claim")),
                    verdict=ClaimVerdict(fc_data["verdict"]),
                    explanation=fc_data["explanation"],
                    citations=citations
                ))
            except KeyError as e:
                print(f"ERROR: Missing key in fact check data: {e}. Data: {fc_data}")
                continue
        
        return SafetyAnalysisResult(
            risk_score=float(data["risk_score"]),
            risk_level=RiskLevel(data["risk_level"]),
            summary=data["summary"],
            key_signals=data["key_signals"],
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
        
        # Token counting approximation
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
