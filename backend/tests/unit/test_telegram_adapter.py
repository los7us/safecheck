"""
Unit tests for TelegramAdapter

Tests URL parsing, pattern matching, and schema conformance.
"""

import pytest
from src.adapters.telegram_adapter import TelegramAdapter
from src.adapters.base_adapter import URLParseError
from src.core.schemas import PlatformName


@pytest.fixture
def telegram_adapter():
    """Create a TelegramAdapter instance for testing"""
    return TelegramAdapter({})


class TestTelegramURLPattern:
    """Tests for URL pattern matching"""
    
    def test_valid_channel_with_message_id(self, telegram_adapter):
        """Should match valid t.me URL with message ID"""
        url = "https://t.me/dulorov_channel/12345"
        assert telegram_adapter.can_handle(url)
    
    def test_valid_channel_without_message_id(self, telegram_adapter):
        """Should match channel URL without message ID"""
        url = "https://t.me/some_channel"
        assert telegram_adapter.can_handle(url)
    
    def test_www_prefix(self, telegram_adapter):
        """Should handle www prefix"""
        url = "https://www.t.me/test_channel/123"
        assert telegram_adapter.can_handle(url)
    
    def test_http_protocol(self, telegram_adapter):
        """Should handle http protocol"""
        url = "http://t.me/channel/456"
        assert telegram_adapter.can_handle(url)
    
    def test_invalid_url_no_channel(self, telegram_adapter):
        """Should not match URL without channel"""
        url = "https://t.me/"
        assert not telegram_adapter.can_handle(url)
    
    def test_different_domain(self, telegram_adapter):
        """Should not match different domains"""
        url = "https://twitter.com/user/12345"
        assert not telegram_adapter.can_handle(url)
    
    def test_telegram_app_link(self, telegram_adapter):
        """Should match standard t.me links"""
        url = "https://t.me/mygroup/789"
        assert telegram_adapter.can_handle(url)


class TestPostIdExtraction:
    """Tests for extracting post ID from URLs"""
    
    def test_extract_channel_and_message(self, telegram_adapter):
        """Should extract channel/message_id format"""
        url = "https://t.me/test_channel/12345"
        post_id = telegram_adapter.get_post_id_from_url(url)
        assert post_id == "test_channel/12345"
    
    def test_extract_channel_only(self, telegram_adapter):
        """Should extract channel name when no message ID"""
        url = "https://t.me/my_channel"
        post_id = telegram_adapter.get_post_id_from_url(url)
        assert post_id == "my_channel"
    
    def test_invalid_url_raises_error(self, telegram_adapter):
        """Should raise URLParseError for invalid URLs"""
        url = "https://twitter.com/invalid"
        with pytest.raises(URLParseError):
            telegram_adapter.get_post_id_from_url(url)


class TestPlatformName:
    """Tests for platform identification"""
    
    def test_platform_name(self, telegram_adapter):
        """Should return TELEGRAM platform"""
        assert telegram_adapter.platform_name == PlatformName.TELEGRAM


class TestHealthCheck:
    """Tests for health check"""
    
    @pytest.mark.asyncio
    async def test_health_check_without_credentials(self, telegram_adapter):
        """Should return False without API credentials"""
        result = await telegram_adapter.health_check()
        assert result is False
    
    @pytest.mark.asyncio
    async def test_health_check_with_credentials(self):
        """Should return True with API credentials configured"""
        adapter = TelegramAdapter({
            "api_id": "12345",
            "api_hash": "abcdef",
        })
        result = await adapter.health_check()
        assert result is True


class TestExtractFromText:
    """Tests for text fallback extraction"""
    
    @pytest.mark.asyncio
    async def test_creates_canonical_post(self, telegram_adapter):
        """Should create valid CanonicalPost from text"""
        text = "This is a test Telegram message"
        post = await telegram_adapter.extract_from_text(text)
        
        assert post.platform_name == PlatformName.TELEGRAM
        assert post.post_text == text
        assert post.post_id.startswith("tg_paste_")
        assert "telegram" in post.adapter_version
