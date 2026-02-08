"""
Manual test script for Gemini analysis.

Tests the full analysis pipeline with real Gemini API.

Usage:
    python scripts/test_gemini_analysis.py
    
Requires GEMINI_API_KEY in .env file.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.core.schemas import (
    CanonicalPost,
    PlatformName,
    MediaFeatures,
    AuthorMetadata,
    AuthorType,
    AccountAgeBucket,
)
from src.services.gemini_service import GeminiService


async def test_scam_detection():
    """Test with obvious scam text"""
    print("\n" + "="*60)
    print("TEST 1: Obvious Investment Scam")
    print("="*60)
    
    post = CanonicalPost(
        post_id="test_scam_1",
        post_text="""
        URGENT INVESTMENT OPPORTUNITY
        
        Guaranteed 10x returns in just 7 days!
        
        Limited spots available - ACT NOW before it's too late!
        
        Send Bitcoin to: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
        
        Don't miss out on this life-changing opportunity!
        """,
        platform_name=PlatformName.REDDIT,
        author_metadata=AuthorMetadata(
            author_type=AuthorType.INDIVIDUAL,
            account_age_bucket=AccountAgeBucket.NEW,
            is_verified=False,
        ),
    )
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set in .env")
        return None
    
    service = GeminiService(api_key=api_key)
    
    try:
        result = await service.analyze(post)
        
        print(f"\nRISK ASSESSMENT:")
        print(f"  Score: {result.risk_score:.2f}")
        print(f"  Level: {result.risk_level.value}")
        
        print(f"\nSUMMARY:")
        print(f"  {result.summary}")
        
        print(f"\nKEY SIGNALS:")
        for signal in result.key_signals:
            print(f"  - {signal}")
        
        if result.fact_checks:
            print(f"\nFACT-CHECKS:")
            for fc in result.fact_checks:
                print(f"  Claim: {fc.claim}")
                print(f"  Verdict: {fc.verdict.value}")
        
        print(f"\nTEST PASSED")
        return result
    
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_legitimate_post():
    """Test with legitimate content"""
    print("\n" + "="*60)
    print("TEST 2: Legitimate Post")
    print("="*60)
    
    post = CanonicalPost(
        post_id="test_legit_1",
        post_text="""
        Just wanted to share my experience learning Python!
        
        Been working through the documentation and it's been really helpful.
        The community here is great. Thanks everyone for the support!
        """,
        platform_name=PlatformName.REDDIT,
        author_metadata=AuthorMetadata(
            author_type=AuthorType.INDIVIDUAL,
            account_age_bucket=AccountAgeBucket.ESTABLISHED,
            is_verified=False,
        ),
    )
    
    api_key = os.getenv("GEMINI_API_KEY")
    service = GeminiService(api_key=api_key)
    
    try:
        result = await service.analyze(post)
        
        print(f"\nRISK ASSESSMENT:")
        print(f"  Score: {result.risk_score:.2f}")
        print(f"  Level: {result.risk_level.value}")
        print(f"  Summary: {result.summary}")
        
        print(f"\nTEST PASSED")
        return result
    
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        return None


async def test_with_media_features():
    """Test with media features (OCR text)"""
    print("\n" + "="*60)
    print("TEST 3: Post with Image containing scam text")
    print("="*60)
    
    post = CanonicalPost(
        post_id="test_media_1",
        post_text="Check out these results!",
        platform_name=PlatformName.TWITTER,
        media_features=MediaFeatures(
            caption="Screenshot (1200x800) containing text",
            ocr_text="EARN $10,000 PER DAY! Click here now! Limited time offer!",
        ),
    )
    
    api_key = os.getenv("GEMINI_API_KEY")
    service = GeminiService(api_key=api_key)
    
    try:
        result = await service.analyze(post)
        
        print(f"\nRISK ASSESSMENT:")
        print(f"  Score: {result.risk_score:.2f}")
        print(f"  Level: {result.risk_level.value}")
        print(f"  Summary: {result.summary}")
        
        print(f"\nKEY SIGNALS:")
        for signal in result.key_signals:
            print(f"  - {signal}")
        
        print(f"\nTEST PASSED - Media features influenced analysis")
        return result
    
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        return None


async def main():
    """Run all tests"""
    print("="*60)
    print("Gemini Analysis Integration Tests")
    print("="*60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("\nERROR: GEMINI_API_KEY not set in .env file")
        print("Please add your Gemini API key to continue.")
        return
    
    results = []
    
    # Run tests
    result1 = await test_scam_detection()
    results.append(("Scam Detection", result1))
    
    result2 = await test_legitimate_post()
    results.append(("Legitimate Post", result2))
    
    result3 = await test_with_media_features()
    results.append(("Media Features", result3))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        if result:
            print(f"  {test_name}: PASS (Risk: {result.risk_level.value})")
        else:
            print(f"  {test_name}: FAIL")
    
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
