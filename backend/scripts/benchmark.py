"""
Performance Benchmark

Measures analysis latency and cache performance.
"""

import asyncio
import time
import statistics
import os
from pathlib import Path
from dotenv import load_dotenv

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.ingestion_pipeline import IngestionPipeline
from src.services.gemini_service import GeminiService
from src.cache.result_cache import ResultCache
from src.adapters.registry import adapter_registry
from src.adapters.reddit_adapter import RedditAdapter

load_dotenv()


async def benchmark_analysis_latency():
    """Benchmark analysis latency"""
    print("\n" + "="*60)
    print("BENCHMARK: Analysis Latency")
    print("="*60)
    
    pipeline = IngestionPipeline(media_cache_dir=Path("./media_cache"))
    gemini_service = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    
    reddit_adapter = RedditAdapter({
        "client_id": os.getenv("REDDIT_CLIENT_ID", "test"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "test"),
    })
    if not adapter_registry.get_adapter("reddit"):
        adapter_registry.register(reddit_adapter)
    
    texts = [
        "URGENT! Limited time investment opportunity!",
        "Check out this cool new restaurant I found",
        "Send Bitcoin to this address for guaranteed returns",
    ]
    
    latencies = []
    
    for i, text in enumerate(texts, 1):
        start = time.time()
        post = await pipeline.ingest_from_text(text, platform_hint="reddit")
        result = await gemini_service.analyze(post)
        latency = time.time() - start
        latencies.append(latency)
        print(f"  Request {i}: {latency:.2f}s (Risk: {result.risk_level.value})")
    
    print(f"\nMean: {statistics.mean(latencies):.2f}s")
    print(f"Median: {statistics.median(latencies):.2f}s")
    print(f"Min/Max: {min(latencies):.2f}s / {max(latencies):.2f}s")
    
    await pipeline.cleanup()
    return latencies


async def benchmark_cache():
    """Benchmark cache performance"""
    print("\n" + "="*60)
    print("BENCHMARK: Cache Performance")
    print("="*60)
    
    pipeline = IngestionPipeline(media_cache_dir=Path("./media_cache"))
    gemini_service = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    cache = ResultCache(backend="memory")
    
    reddit_adapter = RedditAdapter({
        "client_id": os.getenv("REDDIT_CLIENT_ID", "test"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "test"),
    })
    if not adapter_registry.get_adapter("reddit"):
        adapter_registry.register(reddit_adapter)
    
    text = "URGENT investment opportunity!"
    cache_key = cache.generate_cache_key(text=text)
    
    # Cache miss
    start = time.time()
    post = await pipeline.ingest_from_text(text, platform_hint="reddit")
    result = await gemini_service.analyze(post)
    miss_time = time.time() - start
    
    await cache.set(cache_key, result)
    
    # Cache hit
    start = time.time()
    cached = await cache.get(cache_key)
    hit_time = time.time() - start
    
    print(f"Cache miss: {miss_time:.3f}s")
    print(f"Cache hit: {hit_time:.5f}s")
    print(f"Speedup: {miss_time/hit_time:.0f}x")
    
    await pipeline.cleanup()
    await cache.close()


async def main():
    print("\nSafetyCheck Performance Benchmarks")
    print("="*60)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set")
        return
    
    await benchmark_analysis_latency()
    await benchmark_cache()
    
    print("\nBenchmarks complete")


if __name__ == "__main__":
    asyncio.run(main())
