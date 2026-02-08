"""Unit tests for Gemini service"""

import pytest
from datetime import datetime

from src.services.gemini_service import GeminiService
from src.core.schemas import (
    CanonicalPost,
    PlatformName,
    MediaFeatures,
    AuthorMetadata,
    AuthorType,
    AccountAgeBucket,
    EngagementMetrics,
)


class TestPromptBuilding:
    """Test prompt building from CanonicalPost"""
    
    @pytest.fixture
    def gemini_service(self):
        """Create GeminiService with dummy API key"""
        return GeminiService(api_key="test_key_for_unit_tests")
    
    def test_build_prompt_minimal_post(self, gemini_service):
        """Test prompt building with minimal post data"""
        post = CanonicalPost(
            post_id="test_123",
            post_text="Check out this amazing investment opportunity!",
            platform_name=PlatformName.REDDIT,
        )
        
        prompt = gemini_service._build_prompt_from_post(post)
        
        assert "Check out this amazing investment opportunity!" in prompt
        assert "PLATFORM: reddit" in prompt
        assert "POST CONTENT:" in prompt
    
    def test_build_prompt_with_media(self, gemini_service):
        """Test prompt building with media features"""
        post = CanonicalPost(
            post_id="test_123",
            post_text="Guaranteed returns!",
            platform_name=PlatformName.TWITTER,
            media_features=MediaFeatures(
                caption="Screenshot showing financial chart",
                ocr_text="10x returns in 7 days!",
            ),
        )
        
        prompt = gemini_service._build_prompt_from_post(post)
        
        assert "MEDIA CONTENT:" in prompt
        assert "Screenshot showing financial chart" in prompt
        assert "10x returns in 7 days!" in prompt
    
    def test_build_prompt_with_author_metadata(self, gemini_service):
        """Test prompt building with author metadata"""
        post = CanonicalPost(
            post_id="test_123",
            post_text="Test post",
            platform_name=PlatformName.REDDIT,
            author_metadata=AuthorMetadata(
                author_type=AuthorType.INDIVIDUAL,
                account_age_bucket=AccountAgeBucket.NEW,
                is_verified=False,
                follower_count_bucket="0-100",
            ),
        )
        
        prompt = gemini_service._build_prompt_from_post(post)
        
        assert "AUTHOR CONTEXT:" in prompt
        assert "new" in prompt.lower()
        assert "individual" in prompt.lower()
    
    def test_build_prompt_with_engagement(self, gemini_service):
        """Test prompt building with engagement metrics"""
        post = CanonicalPost(
            post_id="test_123",
            post_text="Test post",
            platform_name=PlatformName.TWITTER,
            engagement_metrics=EngagementMetrics(
                likes=100,
                shares=50,
                replies=25,
            ),
        )
        
        prompt = gemini_service._build_prompt_from_post(post)
        
        assert "ENGAGEMENT:" in prompt
        assert "100" in prompt
        assert "50" in prompt
    
    def test_build_prompt_with_external_links(self, gemini_service):
        """Test prompt building with external links"""
        post = CanonicalPost(
            post_id="test_123",
            post_text="Check this out",
            platform_name=PlatformName.REDDIT,
            external_links=[
                "https://sketchy-site.com",
                "https://another-link.com",
            ],
        )
        
        prompt = gemini_service._build_prompt_from_post(post)
        
        assert "EXTERNAL LINKS:" in prompt
        assert "sketchy-site.com" in prompt
