"""
Platform Adapter Base Class

This abstract base class defines the contract that ALL platform adapters
must implement. Any class inheriting from PlatformAdapter can be used
by the ingestion pipeline without modification.

Adapter Responsibilities:
1. Parse platform-specific URLs
2. Extract content using platform API or public scraping
3. Normalize data to CanonicalPost schema
4. Handle platform-specific errors gracefully
5. Respect rate limits and ToS

Adapters must NOT:
- Access private or authenticated content without user permission
- Store PII
- Violate platform Terms of Service
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from src.core.schemas import CanonicalPost, PlatformName
import re


class AdapterException(Exception):
    """Base exception for adapter errors"""
    pass


class URLParseError(AdapterException):
    """Raised when URL cannot be parsed"""
    pass


class ContentExtractionError(AdapterException):
    """Raised when content cannot be extracted"""
    pass


class RateLimitError(AdapterException):
    """Raised when rate limit is hit"""
    pass


class PlatformAdapter(ABC):
    """
    Abstract base class for all platform adapters.
    
    Each platform (Reddit, Twitter, etc.) must implement this interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize adapter with optional configuration.
        
        Args:
            config: Platform-specific configuration (API keys, etc.)
        """
        self.config = config or {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """
        Platform-specific initialization.
        
        Called during __init__. Use this to set up API clients,
        validate credentials, etc.
        """
        pass
    
    @property
    @abstractmethod
    def platform_name(self) -> PlatformName:
        """Return the platform this adapter handles"""
        pass
    
    @property
    @abstractmethod
    def url_pattern(self) -> re.Pattern:
        """
        Return a compiled regex pattern that matches this platform's URLs.
        
        Example:
            re.compile(r'https?://(www\.)?reddit\.com/r/\w+/comments/\w+')
        """
        pass
    
    @abstractmethod
    async def extract(self, url: str) -> CanonicalPost:
        """
        Extract content from a platform URL and normalize to CanonicalPost.
        
        This is the main method that the ingestion pipeline calls.
        
        Args:
            url: Platform-specific URL to extract content from
        
        Returns:
            CanonicalPost with normalized data
        
        Raises:
            URLParseError: If URL format is invalid
            ContentExtractionError: If content cannot be retrieved
            RateLimitError: If rate limit is hit
        """
        pass
    
    def can_handle(self, url: str) -> bool:
        """
        Check if this adapter can handle the given URL.
        
        Args:
            url: URL to check
        
        Returns:
            True if this adapter can handle the URL
        """
        return self.url_pattern.match(url) is not None
    
    @abstractmethod
    def get_post_id_from_url(self, url: str) -> str:
        """
        Extract platform-specific post ID from URL.
        
        Args:
            url: Platform URL
        
        Returns:
            Platform-specific post ID
        
        Raises:
            URLParseError: If URL format is invalid
        """
        pass
    
    @abstractmethod
    async def extract_from_text(self, raw_text: str, context: Optional[Dict[str, Any]] = None) -> CanonicalPost:
        """
        Create CanonicalPost from raw pasted text (fallback mode).
        
        When a user pastes text directly instead of a URL, this method
        creates a minimal CanonicalPost with just the text content.
        
        Args:
            raw_text: The pasted content
            context: Optional metadata (user-provided context)
        
        Returns:
            CanonicalPost with minimal data
        """
        pass
    
    def _get_adapter_version(self) -> str:
        """Return version of this adapter implementation"""
        return "1.0"
    
    async def health_check(self) -> bool:
        """
        Check if adapter is functioning (API accessible, credentials valid, etc.)
        
        Returns:
            True if adapter is healthy
        """
        return True
