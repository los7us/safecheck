"""
Unit tests for Reddit adapter.

Note: These tests use mock data to avoid hitting Reddit API during testing.
Integration tests with real API calls should be separate.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.adapters.reddit_adapter import RedditAdapter
from src.adapters.base_adapter import URLParseError
from src.core.schemas import PlatformName, AccountAgeBucket


@pytest.fixture
def reddit_adapter():
    """Create Reddit adapter with mock credentials"""
    config = {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "user_agent": "test_agent",
    }
    with patch('src.adapters.reddit_adapter.praw.Reddit'):
        adapter = RedditAdapter(config)
        return adapter


class TestRedditAdapterBasics:
    """Test basic adapter properties"""
    
    def test_platform_name(self, reddit_adapter):
        """Test platform name is correct"""
        assert reddit_adapter.platform_name == PlatformName.REDDIT
    
    def test_url_pattern_matching_valid(self, reddit_adapter):
        """Test URL pattern matches valid Reddit URLs"""
        valid_urls = [
            "https://reddit.com/r/python/comments/abc123/test",
            "https://www.reddit.com/r/Python/comments/xyz789/another_test/",
            "https://old.reddit.com/r/test/comments/123abc/old_reddit",
            "https://reddit.com/r/investing/comments/1a2b3c/some_post_title/",
        ]
        
        for url in valid_urls:
            assert reddit_adapter.can_handle(url), f"Should handle: {url}"
    
    def test_url_pattern_matching_invalid(self, reddit_adapter):
        """Test URL pattern rejects invalid URLs"""
        invalid_urls = [
            "https://twitter.com/test",
            "https://reddit.com/user/test",  # User profile, not post
            "https://reddit.com/r/python",  # Subreddit, not post
            "not_a_url",
            "https://example.com",
        ]
        
        for url in invalid_urls:
            assert not reddit_adapter.can_handle(url), f"Should NOT handle: {url}"


class TestRedditAdapterPostId:
    """Test post ID extraction"""
    
    def test_get_post_id_from_url(self, reddit_adapter):
        """Test post ID extraction from URL"""
        url = "https://reddit.com/r/python/comments/abc123/test_post"
        post_id = reddit_adapter.get_post_id_from_url(url)
        assert post_id == "reddit_python_abc123"
    
    def test_get_post_id_with_www(self, reddit_adapter):
        """Test post ID extraction from www URL"""
        url = "https://www.reddit.com/r/investing/comments/xyz789/title"
        post_id = reddit_adapter.get_post_id_from_url(url)
        assert post_id == "reddit_investing_xyz789"
    
    def test_get_post_id_old_reddit(self, reddit_adapter):
        """Test post ID extraction from old.reddit URL"""
        url = "https://old.reddit.com/r/test/comments/aaa111/title"
        post_id = reddit_adapter.get_post_id_from_url(url)
        assert post_id == "reddit_test_aaa111"
    
    def test_get_post_id_invalid_url(self, reddit_adapter):
        """Test post ID extraction fails on invalid URL"""
        with pytest.raises(URLParseError):
            reddit_adapter.get_post_id_from_url("https://twitter.com/test")


class TestRedditAdapterPasteMode:
    """Test paste mode functionality"""
    
    @pytest.mark.asyncio
    async def test_extract_from_text(self, reddit_adapter):
        """Test creating CanonicalPost from pasted text"""
        text = "This is a test post about cryptocurrency"
        post = await reddit_adapter.extract_from_text(text)
        
        assert post.post_text == text
        assert post.platform_name == PlatformName.REDDIT
        assert post.post_id.startswith("reddit_paste_")
        assert post.timestamp is not None
        assert post.adapter_version == "1.0"
    
    @pytest.mark.asyncio
    async def test_extract_from_text_consistent_id(self, reddit_adapter):
        """Test that same text produces same post ID"""
        text = "Consistent text for testing"
        post1 = await reddit_adapter.extract_from_text(text)
        post2 = await reddit_adapter.extract_from_text(text)
        
        assert post1.post_id == post2.post_id
    
    @pytest.mark.asyncio
    async def test_extract_from_text_different_id(self, reddit_adapter):
        """Test that different text produces different post ID"""
        post1 = await reddit_adapter.extract_from_text("Text one")
        post2 = await reddit_adapter.extract_from_text("Text two")
        
        assert post1.post_id != post2.post_id


class TestRedditAdapterMetadataExtraction:
    """Test metadata extraction helpers"""
    
    def test_build_post_text_title_only(self, reddit_adapter):
        """Test post text building with title only"""
        mock_submission = Mock()
        mock_submission.title = "Test Title"
        mock_submission.selftext = ""
        
        text = reddit_adapter._build_post_text(mock_submission)
        assert text == "Test Title"
    
    def test_build_post_text_with_body(self, reddit_adapter):
        """Test post text building with title and body"""
        mock_submission = Mock()
        mock_submission.title = "Test Title"
        mock_submission.selftext = "This is the body text"
        
        text = reddit_adapter._build_post_text(mock_submission)
        assert "Test Title" in text
        assert "This is the body text" in text
    
    def test_extract_engagement_metrics(self, reddit_adapter):
        """Test engagement metrics extraction"""
        mock_submission = Mock()
        mock_submission.score = 150
        mock_submission.num_comments = 42
        
        metrics = reddit_adapter._extract_engagement_metrics(mock_submission)
        
        assert metrics.likes == 150
        assert metrics.replies == 42
        assert metrics.views is None  # Reddit doesn't expose views
    
    def test_extract_engagement_negative_score(self, reddit_adapter):
        """Test engagement handles negative score"""
        mock_submission = Mock()
        mock_submission.score = -10
        mock_submission.num_comments = 5
        
        metrics = reddit_adapter._extract_engagement_metrics(mock_submission)
        
        assert metrics.likes == 0  # Should be clamped to 0
