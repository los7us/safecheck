"""
Canonical Data Schemas v1

These schemas define the normalized structure that ALL platform adapters
must produce. This ensures platform-neutrality and allows the same
analysis pipeline to work across all sources.

Schema Philosophy:
- Required fields: Only what's truly essential (post_id, post_text, platform_name)
- Optional fields: Everything else degrades gracefully
- Timestamps: ISO 8601 strings for serialization
- Enums: Constrained to prevent typos
- Versioning: All schemas include version field
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, HttpUrl, field_validator


# ============================================================================
# ENUMERATIONS
# ============================================================================

class PlatformName(str, Enum):
    """Supported platforms"""
    REDDIT = "reddit"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    UNKNOWN = "unknown"


class MediaType(str, Enum):
    """Types of media content"""
    IMAGE = "image"
    VIDEO = "video"
    GIF = "gif"
    NONE = "none"


class AuthorType(str, Enum):
    """Type of content author"""
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"
    BOT = "bot"
    VERIFIED = "verified"
    UNKNOWN = "unknown"


class AccountAgeBucket(str, Enum):
    """Account age categories (privacy-preserving)"""
    NEW = "new"  # < 30 days
    RECENT = "recent"  # 30 days - 6 months
    ESTABLISHED = "established"  # 6 months - 2 years
    VETERAN = "veteran"  # > 2 years
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Risk assessment levels"""
    MINIMAL = "Minimal"  # 0.0 - 0.25
    LOW = "Low"  # 0.25 - 0.5
    MODERATE = "Moderate"  # 0.5 - 0.7
    HIGH = "High"  # 0.7 - 0.9
    CRITICAL = "Critical"  # 0.9 - 1.0


class ClaimVerdict(str, Enum):
    """Fact-check verdict options"""
    TRUE = "True"
    FALSE = "False"
    MISLEADING = "Misleading"
    UNVERIFIABLE = "Unverifiable"
    LACKS_CONTEXT = "Lacks Context"


# ============================================================================
# MEDIA SCHEMAS
# ============================================================================

class MediaMetadata(BaseModel):
    """Metadata about a single media item"""
    media_type: MediaType
    url: str
    hash: Optional[str] = None  # Content hash for deduplication
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    thumbnail_url: Optional[str] = None


class MediaFeatures(BaseModel):
    """Derived features from media processing"""
    caption: Optional[str] = None  # Image captioning output
    ocr_text: Optional[str] = None  # Extracted text from image
    detected_objects: Optional[List[str]] = None
    nsfw_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    face_detected: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "caption": "A screenshot of a financial chart",
                "ocr_text": "Guaranteed 1000% returns in 7 days!",
                "detected_objects": ["chart", "text", "logo"],
                "nsfw_score": 0.05,
                "face_detected": False
            }
        }


# ============================================================================
# METADATA SCHEMAS
# ============================================================================

class EngagementMetrics(BaseModel):
    """Public engagement metrics (if available)"""
    likes: Optional[int] = Field(None, ge=0)
    shares: Optional[int] = Field(None, ge=0)
    replies: Optional[int] = Field(None, ge=0)
    views: Optional[int] = Field(None, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "likes": 523,
                "shares": 89,
                "replies": 156,
                "views": 12453
            }
        }


class AuthorMetadata(BaseModel):
    """Non-PII author information"""
    author_type: AuthorType = AuthorType.UNKNOWN
    account_age_bucket: AccountAgeBucket = AccountAgeBucket.UNKNOWN
    is_verified: Optional[bool] = None
    follower_count_bucket: Optional[str] = None  # "0-100", "100-1k", "1k-10k", etc.
    
    class Config:
        json_schema_extra = {
            "example": {
                "author_type": "individual",
                "account_age_bucket": "new",
                "is_verified": False,
                "follower_count_bucket": "0-100"
            }
        }


# ============================================================================
# CANONICAL POST SCHEMA (PRIMARY INPUT)
# ============================================================================

class CanonicalPost(BaseModel):
    """
    The normalized post structure that ALL platform adapters must produce.
    
    This is the contract between platform adapters and the analysis engine.
    
    Required fields:
    - post_id: Unique identifier
    - post_text: The actual content
    - platform_name: Source platform
    
    Everything else is optional and degrades gracefully.
    """
    
    # Required fields
    post_id: str = Field(..., description="Unique identifier for this post")
    post_text: str = Field(..., description="The actual text content")
    platform_name: PlatformName = Field(..., description="Source platform")
    
    # Temporal
    timestamp: Optional[datetime] = Field(None, description="When post was created (ISO 8601)")
    
    # Language
    language: Optional[str] = Field(None, description="ISO 639-1 language code (e.g., 'en', 'es')")
    
    # Author metadata (non-PII)
    author_metadata: Optional[AuthorMetadata] = None
    
    # Engagement
    engagement_metrics: Optional[EngagementMetrics] = None
    
    # Media content
    media_items: Optional[List[MediaMetadata]] = Field(default_factory=list)
    media_features: Optional[MediaFeatures] = None
    
    # Context
    external_links: Optional[List[str]] = Field(default_factory=list)
    hashtags: Optional[List[str]] = Field(default_factory=list)
    mentions: Optional[List[str]] = Field(default_factory=list)
    
    # Optional context
    sampled_comments: Optional[List[str]] = Field(default_factory=list, max_length=5)
    reply_context: Optional[str] = None  # If this is a reply, what's it replying to?
    
    # Metadata
    raw_url: Optional[str] = None  # Original URL if applicable
    adapter_version: str = Field(default="1.0", description="Version of adapter that produced this")
    
    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "reddit_abc123",
                "post_text": "Invest in XYZ coin now! Guaranteed 10x returns in 7 days or your money back!",
                "platform_name": "reddit",
                "timestamp": "2024-02-08T10:30:00Z",
                "language": "en",
                "author_metadata": {
                    "author_type": "individual",
                    "account_age_bucket": "new",
                    "is_verified": False,
                    "follower_count_bucket": "0-100"
                },
                "engagement_metrics": {
                    "likes": 3,
                    "replies": 45,
                    "views": 1200
                },
                "media_items": [
                    {
                        "media_type": "image",
                        "url": "https://example.com/chart.png",
                        "hash": "sha256_abc123"
                    }
                ],
                "external_links": ["https://sketchy-crypto-site.com"],
                "hashtags": ["crypto", "investing"],
                "raw_url": "https://reddit.com/r/example/comments/abc123"
            }
        }


# ============================================================================
# ANALYSIS OUTPUT SCHEMAS
# ============================================================================

class Citation(BaseModel):
    """A credible source citation"""
    source_name: str = Field(..., description="Name of the source (e.g., 'U.S. SEC')")
    url: HttpUrl = Field(..., description="Link to the source")
    excerpt: Optional[str] = Field(None, description="Brief relevant excerpt", max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_name": "U.S. Securities and Exchange Commission",
                "url": "https://www.sec.gov/investor/alerts/ia_virtualcurrencies.pdf",
                "excerpt": "Be wary of investments offering guaranteed high returns"
            }
        }


class FactCheck(BaseModel):
    """A single fact-checked claim"""
    claim: str = Field(..., description="The specific claim being checked")
    verdict: ClaimVerdict = Field(..., description="Assessment of the claim")
    explanation: str = Field(..., description="Why this verdict was reached", max_length=500)
    citations: List[Citation] = Field(default_factory=list, description="Supporting sources")
    
    @field_validator('citations')
    @classmethod
    def validate_citations(cls, v):
        if len(v) == 0:
            raise ValueError("At least one citation required for fact-checks")
        if len(v) > 3:
            raise ValueError("Maximum 3 citations per fact-check")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "claim": "Guaranteed 10x return in 7 days",
                "verdict": "False",
                "explanation": "No legitimate investment can guarantee specific returns, especially extremely high returns in short timeframes. This is a common scam tactic.",
                "citations": [
                    {
                        "source_name": "U.S. SEC Investor Alerts",
                        "url": "https://www.sec.gov/investor/alerts",
                        "excerpt": "Promises of guaranteed returns are red flags"
                    }
                ]
            }
        }


class SafetyAnalysisResult(BaseModel):
    """
    The complete output from Gemini safety analysis.
    
    This is the contract between the Gemini service and the frontend.
    """
    
    # Risk assessment
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Overall risk probability (0-1)")
    risk_level: RiskLevel = Field(..., description="Human-readable risk category")
    
    # Explanation
    summary: str = Field(..., description="Concise explanation of the assessment", max_length=500)
    key_signals: List[str] = Field(..., description="2-5 specific indicators that informed the score", min_length=2, max_length=5)
    
    # Fact-checking (conditional)
    fact_checks: List[FactCheck] = Field(default_factory=list, description="Only populated if verifiable claims detected")
    
    # Metadata
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(default="gemini-1.5-pro", description="Gemini model used")
    
    @field_validator('risk_score')
    @classmethod
    def risk_score_matches_level(cls, v, info):
        """Ensure risk_level matches risk_score"""
        if 'risk_level' in info.data:
            level = info.data['risk_level']
            if level == RiskLevel.MINIMAL and not (0.0 <= v < 0.25):
                raise ValueError(f"Risk score {v} doesn't match level {level}")
            elif level == RiskLevel.LOW and not (0.25 <= v < 0.5):
                raise ValueError(f"Risk score {v} doesn't match level {level}")
            elif level == RiskLevel.MODERATE and not (0.5 <= v < 0.7):
                raise ValueError(f"Risk score {v} doesn't match level {level}")
            elif level == RiskLevel.HIGH and not (0.7 <= v < 0.9):
                raise ValueError(f"Risk score {v} doesn't match level {level}")
            elif level == RiskLevel.CRITICAL and not (0.9 <= v <= 1.0):
                raise ValueError(f"Risk score {v} doesn't match level {level}")
        return v
    
    class Config:
        protected_namespaces = ()  # Allow 'model_' prefix for model_version field
        json_schema_extra = {
            "example": {
                "risk_score": 0.85,
                "risk_level": "High",
                "summary": "This post exhibits multiple characteristics of a cryptocurrency investment scam, including unrealistic return promises and urgency tactics.",
                "key_signals": [
                    "Guaranteed high returns (10x in 7 days)",
                    "Urgency framing ('Act now!')",
                    "New account with low credibility",
                    "External link to unverified site",
                    "Common scam language patterns"
                ],
                "fact_checks": [
                    {
                        "claim": "Guaranteed 10x return in 7 days",
                        "verdict": "False",
                        "explanation": "No legitimate investment can guarantee returns.",
                        "citations": [
                            {
                                "source_name": "U.S. SEC",
                                "url": "https://www.sec.gov/investor/alerts"
                            }
                        ]
                    }
                ],
                "analysis_timestamp": "2024-02-08T10:35:00Z",
                "model_version": "gemini-1.5-pro"
            }
        }


# ============================================================================
# SCHEMA VERSION REGISTRY
# ============================================================================


# ============================================================================
# API SCHEMAS
# ============================================================================

class AnalysisRequest(BaseModel):
    """Request with strict validation"""
    
    url: Optional[str] = Field(None, max_length=2000)
    text: Optional[str] = Field(None, max_length=50000)  # ~50KB
    platform_hint: Optional[str] = Field(None, max_length=50)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if v is None:
            return v
        
        # Check URL scheme
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        
        # Reject potentially dangerous schemes
        dangerous_schemes = ['file://', 'javascript:', 'data:', 'vbscript:']
        if any(v.lower().startswith(scheme) for scheme in dangerous_schemes):
            raise ValueError('Invalid URL scheme')
        
        # Reject localhost/internal IPs (SSRF protection)
        from urllib.parse import urlparse
        parsed = urlparse(v)
        
        # Block localhost (basic check)
        if parsed.hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
            raise ValueError('Cannot analyze localhost URLs')
        
        # Block private IP ranges (basic check)
        if parsed.hostname and (
            parsed.hostname.startswith(('10.', '172.16.', '192.168.')) or
            parsed.hostname.startswith('172.') and 16 <= int(parsed.hostname.split('.')[1]) <= 31
        ):
            # Slightly improved check for 172.16-31
            raise ValueError('Cannot analyze private IP addresses')
            
        return v
    
    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if v is None:
            return v
        
        # Reject empty text
        if not v.strip():
            raise ValueError('Text cannot be empty')
        
        # Check for null bytes
        if '\x00' in v:
            raise ValueError('Invalid characters in text')
        
        return v
    
    @field_validator('platform_hint')
    @classmethod
    def validate_platform(cls, v):
        if v is None:
            return v
        
        allowed_platforms = ['reddit', 'twitter', 'facebook', 'instagram', 'tiktok', 'youtube']
        if v.lower() not in allowed_platforms:
            # For robust production, perhaps allow 'unknown' or warn log, 
            # but strict validation is safer.
            # I'll allow 'unknown' if it's explicitly passed, or reject garbage.
            raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        
        return v.lower()


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint"""
    success: bool
    data: Optional[SafetyAnalysisResult] = None
    error: Optional[str] = None
    cached: bool = False

SCHEMA_VERSION = "1.0.0"

# Export all schemas
__all__ = [
    # Enums
    "PlatformName",
    "MediaType",
    "AuthorType",
    "AccountAgeBucket",
    "RiskLevel",
    "ClaimVerdict",
    # Media
    "MediaMetadata",
    "MediaFeatures",
    # Metadata
    "EngagementMetrics",
    "AuthorMetadata",
    # Primary schemas
    "CanonicalPost",
    "SafetyAnalysisResult",
    "FactCheck",
    "Citation",
    # API
    "AnalysisRequest",
    "AnalysisResponse",
    # Version
    "SCHEMA_VERSION",
]
