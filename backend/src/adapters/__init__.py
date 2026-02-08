"""
Adapter module initialization.

Registers all platform adapters.
"""

from src.adapters.base_adapter import (
    PlatformAdapter,
    AdapterException,
    URLParseError,
    ContentExtractionError,
    RateLimitError,
)
from src.adapters.reddit_adapter import RedditAdapter
from src.adapters.twitter_adapter import TwitterAdapter
from src.adapters.registry import adapter_registry, AdapterRegistry

# Platform adapters will be registered in main.py after config is loaded

__all__ = [
    # Base
    "PlatformAdapter",
    "AdapterException",
    "URLParseError",
    "ContentExtractionError",
    "RateLimitError",
    # Adapters
    "RedditAdapter",
    "TwitterAdapter",
    # Registry
    "adapter_registry",
    "AdapterRegistry",
]
