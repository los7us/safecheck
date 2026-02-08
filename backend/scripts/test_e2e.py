"""
End-to-End Test Script

Tests complete flow: URL/text -> Adapter -> Media -> Gemini -> Result
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.ingestion_pipeline import IngestionPipeline
from src.services.gemini_service import GeminiService
from src.cache.result_cache import ResultCache
from src.monitoring.metrics import MetricsTracker
from src.adapters.registry import adapter_registry
from src.adapters.reddit_adapter import RedditAdapter

load_dotenv()


async def test_text_analysis():
    """Test analysis with pasted text"""
    print("\n" + "="*60)
    print("TEST 1: Text Analysis + Caching")
    print("="*60)
    
    media_cache_dir = Path("./media_cache")
    media_cache_dir.mkdir(exist_ok=True)
    
    pipeline = IngestionPipeline(media_cache_dir=media_cache_dir)
    gemini_service = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    cache = ResultCache(backend="memory")
    metrics = MetricsTracker()
    
    reddit_adapter = RedditAdapter({
        "client_id": os.getenv("REDDIT_CLIENT_ID", "test"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "test"),
    })
    adapter_registry.register(reddit_adapter)
    
    scam_text = """
    URGENT INVESTMENT OPPORTUNITY!
    Make $10,000+ per week guaranteed!
    Limited spots - act NOW!
    """
    
    try:
        cache_key = cache.generate_cache_key(text=scam_text)
        
        # First request (cache miss)
        print("\nFirst request (cache miss)...")
        import time
        start = time.time()
        
        post = await pipeline.ingest_from_text(scam_text, platform_hint="reddit")
        result = await gemini_service.analyze(post)
        
        latency1 = time.time() - start
        
        print(f"Analysis complete in {latency1:.2f}s")
        print(f"  Risk: {result.risk_level.value} ({result.risk_score:.2f})")
        
        await cache.set(cache_key, result)
        metrics.record_request(latency=latency1, tokens=500)
        metrics.record_cache_miss()
        
        # Second request (cache hit)
        print("\nSecond request (cache hit)...")
        start = time.time()
        
        cached_result = await cache.get(cache_key)
        
        latency2 = time.time() - start
        
        print(f"Cache retrieval in {latency2:.4f}s")
        print(f"Speedup: {latency1/latency2:.0f}x faster")
        
        metrics.record_cache_hit()
        
        assert cached_result is not None
        assert cached_result.risk_score == result.risk_score
        
        print("\nMetrics:")
        cache_stats = metrics.get_cache_stats()
        print(f"  Cache hit rate: {cache_stats['hit_rate']:.1%}")
        
        print("\nTEST PASSED")
        return True
    
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await pipeline.cleanup()
        await cache.close()


async def test_rate_limiting():
    """Test rate limit enforcement"""
    print("\n" + "="*60)
    print("TEST 2: Rate Limiting")
    print("="*60)
    
    metrics = MetricsTracker(hourly_request_limit=3, daily_request_limit=5)
    
    for i in range(3):
        allowed = metrics.check_rate_limit()
        print(f"Request {i+1}: {'Allowed' if allowed else 'Blocked'}")
        assert allowed == True
        metrics.record_request(latency=1.0, tokens=100)
    
    allowed = metrics.check_rate_limit()
    print(f"Request 4: {'Allowed' if allowed else 'Blocked'}")
    assert allowed == False
    
    print("\nTEST PASSED")
    return True


async def main():
    """Run all E2E tests"""
    print("\n" + "="*60)
    print("SafetyCheck End-to-End Tests")
    print("="*60)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("\nERROR: GEMINI_API_KEY not set")
        return
    
    results = []
    
    results.append(("Text Analysis + Caching", await test_text_analysis()))
    results.append(("Rate Limiting", await test_rate_limiting()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
