"""Unit tests for Twitter adapter"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.adapters.twitter_adapter import TwitterAdapter
from src.adapters.base_adapter import URLParseError
from src.core.schemas import PlatformName


@pytest.fixture
def twitter_adapter():
    """Create Twitter adapter without credentials (paste mode only)"""
    config = {}
    adapter = TwitterAdapter(config)
    return adapter


@pytest.fixture
def twitter_adapter_with_api():
    """Create Twitter adapter with mocked API"""
    config = {"bearer_token": "test_token"}
    with patch('src.adapters.twitter_adapter.tweepy') as mock_tweepy:
        mock_client = Mock()
        mock_tweepy.Client.return_value = mock_client
        adapter = TwitterAdapter(config)
        return adapter


class TestTwitterAdapterBasics:
    """Test basic adapter properties"""
    
    def test_platform_name(self, twitter_adapter):
        """Test platform name is correct"""
        assert twitter_adapter.platform_name == PlatformName.TWITTER
    
    def test_url_pattern_matching_valid(self, twitter_adapter):
        """Test URL pattern matches valid Twitter URLs"""
        valid_urls = [
            "https://twitter.com/user/status/123456789",
            "https://x.com/user/status/987654321",
            "https://www.twitter.com/testuser/status/111222333",
            "https://twitter.com/elonmusk/status/1234567890123456789",
            "https://x.com/someone/status/9999999999?s=20",
        ]
        
        for url in valid_urls:
            assert twitter_adapter.can_handle(url), f"Should handle: {url}"
    
    def test_url_pattern_matching_invalid(self, twitter_adapter):
        """Test URL pattern rejects invalid URLs"""
        invalid_urls = [
            "https://reddit.com/r/test",
            "https://twitter.com/user",  # No status
            "https://twitter.com/user/followers",
            "not_a_url",
        ]
        
        for url in invalid_urls:
            assert not twitter_adapter.can_handle(url), f"Should NOT handle: {url}"


class TestTwitterAdapterPostId:
    """Test post ID extraction"""
    
    def test_get_post_id_from_url(self, twitter_adapter):
        """Test post ID extraction from URL"""
        url = "https://twitter.com/testuser/status/123456789"
        post_id = twitter_adapter.get_post_id_from_url(url)
        assert post_id == "twitter_testuser_123456789"
    
    def test_get_post_id_from_x_url(self, twitter_adapter):
        """Test post ID extraction from x.com URL"""
        url = "https://x.com/anotheruser/status/987654321"
        post_id = twitter_adapter.get_post_id_from_url(url)
        assert post_id == "twitter_anotheruser_987654321"
    
    def test_get_post_id_with_query_params(self, twitter_adapter):
        """Test post ID extraction with query parameters"""
        url = "https://twitter.com/user/status/111222333?s=20&t=abc"
        post_id = twitter_adapter.get_post_id_from_url(url)
        assert post_id == "twitter_user_111222333"
    
    def test_get_post_id_invalid_url(self, twitter_adapter):
        """Test post ID extraction fails on invalid URL"""
        with pytest.raises(URLParseError):
            twitter_adapter.get_post_id_from_url("https://reddit.com/r/test")


class TestTwitterAdapterPasteMode:
    """Test paste mode functionality"""
    
    @pytest.mark.asyncio
    async def test_extract_from_text(self, twitter_adapter):
        """Test creating CanonicalPost from pasted text"""
        text = "This is a test tweet about crypto investment opportunities!"
        post = await twitter_adapter.extract_from_text(text)
        
        assert post.post_text == text
        assert post.platform_name == PlatformName.TWITTER
        assert post.post_id.startswith("twitter_paste_")
        assert post.timestamp is not None
        assert post.adapter_version == "1.0"
    
    @pytest.mark.asyncio
    async def test_extract_from_text_consistent_id(self, twitter_adapter):
        """Test that same text produces same post ID"""
        text = "Consistent tweet text"
        post1 = await twitter_adapter.extract_from_text(text)
        post2 = await twitter_adapter.extract_from_text(text)
        
        assert post1.post_id == post2.post_id
    
    @pytest.mark.asyncio
    async def test_extract_from_text_with_context(self, twitter_adapter):
        """Test extract_from_text with optional context"""
        text = "Tweet with context"
        context = {"source": "user_paste"}
        post = await twitter_adapter.extract_from_text(text, context)
        
        assert post.post_text == text


class TestTwitterAdapterConfiguration:
    """Test adapter configuration"""
    
    def test_no_api_token_uses_scraping(self):
        """Test adapter falls back to scraping without API token"""
        adapter = TwitterAdapter({})
        assert adapter.use_api is False
        assert adapter.client is None
    
    def test_default_nitter_instance(self):
        """Test default nitter instance is set"""
        adapter = TwitterAdapter({})
        assert adapter.nitter_instance == "https://nitter.net"
    
    def test_custom_nitter_instance(self):
        """Test custom nitter instance can be set"""
        adapter = TwitterAdapter({"nitter_instance": "https://custom.nitter.instance"})
        assert adapter.nitter_instance == "https://custom.nitter.instance"


class TestTwitterAdapterMediaExtraction:
    """Test media extraction helpers"""
    
    def test_extract_media_scraping_empty(self, twitter_adapter):
        """Test media extraction with no media"""
        mock_soup = Mock()
        mock_soup.find_all.return_value = []
        
        media = twitter_adapter._extract_media_scraping(mock_soup)
        assert media == []
