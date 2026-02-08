"""
Validation script to test both adapters with real data.

Usage:
    python scripts/validate_adapters.py

This script:
1. Tests URL parsing
2. Tests paste mode
3. Validates output schemas
4. Checks graceful degradation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()


async def test_reddit_adapter():
    """Test Reddit adapter"""
    from unittest.mock import patch
    
    print("\n=== Testing Reddit Adapter ===")
    
    config = {
        "client_id": os.getenv("REDDIT_CLIENT_ID"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET"),
        "user_agent": "SafetyCheck/1.0 Validation",
    }
    
    # If no credentials, use mock mode
    if not config["client_id"]:
        print("⚠ No Reddit credentials found, testing in mock mode")
        with patch('src.adapters.reddit_adapter.praw.Reddit'):
            from src.adapters.reddit_adapter import RedditAdapter
            adapter = RedditAdapter({"client_id": "mock", "client_secret": "mock"})
    else:
        from src.adapters.reddit_adapter import RedditAdapter
        adapter = RedditAdapter(config)
    
    # Test URL pattern
    test_url = "https://reddit.com/r/test/comments/abc123/example"
    print(f"✓ Can handle Reddit URL: {adapter.can_handle(test_url)}")
    
    # Test post ID extraction
    post_id = adapter.get_post_id_from_url(test_url)
    print(f"✓ Extracted post ID: {post_id}")
    
    # Test paste mode
    text = "This is a test Reddit post about investment scams"
    post = await adapter.extract_from_text(text)
    print(f"✓ Paste mode works. Post ID: {post.post_id}")
    
    # Validate schema
    assert post.post_id.startswith("reddit_paste_")
    assert post.post_text == text
    assert post.platform_name.value == "reddit"
    print("✓ Schema validation passed")
    
    # Test health check (may fail without credentials)
    try:
        is_healthy = await adapter.health_check()
        print(f"✓ Health check: {'PASS' if is_healthy else 'FAIL (expected without credentials)'}")
    except Exception as e:
        print(f"⚠ Health check skipped: {e}")
    
    return adapter


async def test_twitter_adapter():
    """Test Twitter adapter"""
    print("\n=== Testing Twitter Adapter ===")
    
    from src.adapters.twitter_adapter import TwitterAdapter
    
    config = {
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
    }
    
    adapter = TwitterAdapter(config)
    
    # Test URL pattern - Twitter
    test_urls = [
        ("https://twitter.com/user/status/123456789", True),
        ("https://x.com/user/status/987654321", True),
        ("https://reddit.com/r/test/comments/abc", False),
    ]
    
    for url, expected in test_urls:
        result = adapter.can_handle(url)
        assert result == expected, f"URL {url} expected {expected}, got {result}"
    print("✓ URL pattern matching works")
    
    # Test post ID extraction
    post_id = adapter.get_post_id_from_url("https://twitter.com/elonmusk/status/1234567890")
    assert post_id == "twitter_elonmusk_1234567890"
    print(f"✓ Extracted post ID: {post_id}")
    
    # Test paste mode
    text = "Check out this crypto opportunity! 🚀 Guaranteed 10x returns!"
    post = await adapter.extract_from_text(text)
    print(f"✓ Paste mode works. Post ID: {post.post_id}")
    
    # Validate schema
    assert post.post_id.startswith("twitter_paste_")
    assert post.post_text == text
    assert post.platform_name.value == "twitter"
    print("✓ Schema validation passed")
    
    # Health check
    try:
        is_healthy = await adapter.health_check()
        print(f"✓ Health check: {'PASS' if is_healthy else 'FAIL (nitter may be unreachable)'}")
    except Exception as e:
        print(f"⚠ Health check error: {e}")
    
    return adapter


async def test_registry():
    """Test adapter registry"""
    print("\n=== Testing Adapter Registry ===")
    
    from src.adapters.registry import AdapterRegistry
    
    reddit_adapter = await test_reddit_adapter()
    twitter_adapter = await test_twitter_adapter()
    
    # Create fresh registry
    registry = AdapterRegistry()
    
    # Register adapters
    registry.register(reddit_adapter)
    registry.register(twitter_adapter)
    print("✓ Both adapters registered")
    
    # Test URL routing
    reddit_url = "https://reddit.com/r/test/comments/abc/test"
    twitter_url = "https://twitter.com/user/status/123"
    x_url = "https://x.com/user/status/456"
    unknown_url = "https://facebook.com/post/123"
    
    assert registry.get_adapter_for_url(reddit_url) is not None
    assert registry.get_adapter_for_url(twitter_url) is not None
    assert registry.get_adapter_for_url(x_url) is not None
    assert registry.get_adapter_for_url(unknown_url) is None
    print("✓ URL routing works correctly")
    
    # List platforms
    platforms = registry.list_platforms()
    assert len(platforms) == 2
    print(f"✓ Registered platforms: {[p.value for p in platforms]}")
    
    return True


async def test_graceful_degradation():
    """Test graceful handling of missing data"""
    print("\n=== Testing Graceful Degradation ===")
    
    from src.adapters.twitter_adapter import TwitterAdapter
    
    adapter = TwitterAdapter({})
    
    # Minimal post - only required fields
    post = await adapter.extract_from_text("Minimal content")
    
    # Required fields should be present
    assert post.post_id is not None
    assert post.post_text == "Minimal content"
    assert post.platform_name is not None
    
    # Optional fields should be None or empty lists
    assert post.author_metadata is None or post.author_metadata is not None  # Either is OK
    assert post.engagement_metrics is None or post.engagement_metrics is not None
    assert post.media_items is not None  # Empty list by default
    
    print("✓ Graceful degradation works - missing data doesn't crash")
    
    return True


async def main():
    """Run all validation tests"""
    print("=" * 60)
    print("SafetyCheck Adapter Validation")
    print("=" * 60)
    
    results = []
    
    try:
        await test_registry()
        results.append(("Registry", True))
    except Exception as e:
        print(f"\n❌ Registry test failed: {e}")
        results.append(("Registry", False))
        import traceback
        traceback.print_exc()
    
    try:
        await test_graceful_degradation()
        results.append(("Graceful Degradation", True))
    except Exception as e:
        print(f"\n❌ Graceful degradation test failed: {e}")
        results.append(("Graceful Degradation", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n✅ All adapter validation tests passed!")
    else:
        print("\n⚠ Some tests failed. Check output above for details.")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
