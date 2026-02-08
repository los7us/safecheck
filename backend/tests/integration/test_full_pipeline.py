"""
Integration test for complete analysis pipeline.

Tests: Adapter -> Media Processing -> Gemini Analysis
"""

import pytest
import os
from pathlib import Path

from src.core.schemas import CanonicalPost, PlatformName


@pytest.mark.skipif(
    os.getenv('SKIP_INTEGRATION_TESTS', '0') == '1' or not os.getenv('GEMINI_API_KEY'),
    reason="Integration tests skipped or missing API keys"
)
@pytest.mark.asyncio
async def test_full_pipeline_paste_mode():
    """Test full pipeline with paste mode"""
    from src.services.ingestion_pipeline import IngestionPipeline
    from src.services.gemini_service import GeminiService
    from src.adapters.twitter_adapter import TwitterAdapter
    from src.adapters.registry import adapter_registry
    
    # Setup
    twitter_adapter = TwitterAdapter({})
    adapter_registry.register(twitter_adapter)
    
    pipeline = IngestionPipeline(media_cache_dir=Path("./media_cache"))
    gemini_service = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Ingest scam content
    scam_text = "URGENT! Send me Bitcoin for 10x guaranteed returns in 24 hours!"
    post = await pipeline.ingest_from_text(scam_text)
    
    # Analyze
    result = await gemini_service.analyze(post)
    
    # Verify high risk detected
    assert result.risk_score > 0.5
    assert result.risk_level.value in ["Moderate", "High", "Critical"]
    assert len(result.key_signals) >= 2
    
    print(f"Full pipeline test passed")
    print(f"  Risk: {result.risk_level.value} ({result.risk_score:.2f})")
    
    # Cleanup
    await pipeline.cleanup()


@pytest.mark.skipif(
    os.getenv('SKIP_INTEGRATION_TESTS', '0') == '1' or not os.getenv('GEMINI_API_KEY'),
    reason="Integration tests skipped or missing API keys"
)
@pytest.mark.asyncio
async def test_legitimate_content_low_risk():
    """Test that legitimate content scores low"""
    from src.services.gemini_service import GeminiService
    
    gemini_service = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    
    post = CanonicalPost(
        post_id="test_legit",
        post_text="I love learning Python! The community is so helpful.",
        platform_name=PlatformName.REDDIT,
    )
    
    result = await gemini_service.analyze(post)
    
    # Should be low risk
    assert result.risk_score < 0.5
    assert result.risk_level.value in ["Minimal", "Low"]
    
    print(f"Legitimate content test passed")
    print(f"  Risk: {result.risk_level.value} ({result.risk_score:.2f})")
