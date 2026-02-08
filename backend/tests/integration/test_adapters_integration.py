"""
Integration tests for platform adapters.

These tests use REAL URLs to verify adapters work correctly.
They should be run separately from unit tests and may be slow.

Set SKIP_INTEGRATION_TESTS=1 to skip these in CI.
"""

import os
import pytest

# Skip if no credentials or SKIP_INTEGRATION_TESTS is set
SKIP_INTEGRATION = os.getenv('SKIP_INTEGRATION_TESTS', '0') == '1'
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')


@pytest.mark.skipif(
    SKIP_INTEGRATION or not REDDIT_CLIENT_ID,
    reason="Integration tests skipped or missing credentials"
)
@pytest.mark.asyncio
async def test_reddit_adapter_real_post():
    """Test Reddit adapter with a real post"""
    from src.adapters.reddit_adapter import RedditAdapter
    
    config = {
        "client_id": REDDIT_CLIENT_ID,
        "client_secret": REDDIT_CLIENT_SECRET,
        "user_agent": "SafetyCheck/1.0 Integration Test",
    }
    
    adapter = RedditAdapter(config)
    
    # Use a stable, public, pinned post from r/announcements
    url = "https://www.reddit.com/r/announcements/comments/8bb85p/reddits_2017_transparency_report_and_suspect/"
    
    try:
        post = await adapter.extract(url)
        
        # Validate schema
        assert post.post_id
        assert post.post_text
        assert post.platform_name.value == "reddit"
        assert post.timestamp is not None
        
        print(f"✓ Extracted Reddit post: {post.post_id}")
        print(f"  Text preview: {post.post_text[:100]}...")
        
    except Exception as e:
        pytest.fail(f"Reddit adapter integration test failed: {e}")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests skipped")
@pytest.mark.asyncio
async def test_twitter_adapter_paste_mode():
    """Test Twitter adapter in paste mode (no credentials needed)"""
    from src.adapters.twitter_adapter import TwitterAdapter
    
    adapter = TwitterAdapter({})
    
    text = "This is a test tweet about cryptocurrency investment opportunities! 🚀"
    post = await adapter.extract_from_text(text)
    
    assert post.post_text == text
    assert post.platform_name.value == "twitter"
    
    print("✓ Twitter adapter paste mode works")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests skipped")
@pytest.mark.asyncio
async def test_reddit_adapter_paste_mode():
    """Test Reddit adapter in paste mode (no credentials needed)"""
    from unittest.mock import patch
    
    with patch('src.adapters.reddit_adapter.praw.Reddit'):
        from src.adapters.reddit_adapter import RedditAdapter
        
        adapter = RedditAdapter({
            "client_id": "mock",
            "client_secret": "mock",
        })
        
        text = "Investment opportunity! Double your money in 24 hours! DM me now!"
        post = await adapter.extract_from_text(text)
        
        assert post.post_text == text
        assert post.platform_name.value == "reddit"
        
        print("✓ Reddit adapter paste mode works")


@pytest.mark.skipif(SKIP_INTEGRATION, reason="Integration tests skipped")
@pytest.mark.asyncio
async def test_adapter_registry_routing():
    """Test adapter registry routes URLs correctly"""
    from unittest.mock import patch
    from src.adapters.registry import AdapterRegistry
    from src.adapters.twitter_adapter import TwitterAdapter
    
    registry = AdapterRegistry()
    
    # Register Twitter adapter (no mock needed - no credentials)
    twitter = TwitterAdapter({})
    registry.register(twitter)
    
    # Test URL routing
    twitter_url = "https://twitter.com/user/status/123456789"
    x_url = "https://x.com/user/status/987654321"
    reddit_url = "https://reddit.com/r/test/comments/abc123/title"
    
    assert registry.get_adapter_for_url(twitter_url) is not None
    assert registry.get_adapter_for_url(x_url) is not None
    assert registry.get_adapter_for_url(reddit_url) is None  # No Reddit adapter registered
    
    print("✓ Adapter registry routing works")
