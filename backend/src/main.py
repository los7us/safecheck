"""
SafetyCheck API Main Application

FastAPI server providing endpoints for content analysis.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import os
import time
from pathlib import Path
from dotenv import load_dotenv

from src.core.schemas import SafetyAnalysisResult
from src.services.ingestion_pipeline import IngestionPipeline
from src.services.gemini_service import GeminiService
from src.adapters.registry import adapter_registry
from src.adapters.reddit_adapter import RedditAdapter
from src.adapters.twitter_adapter import TwitterAdapter
from src.cache.result_cache import ResultCache
from src.monitoring.metrics import MetricsTracker

load_dotenv()


# API Request/Response Models
class AnalysisRequest(BaseModel):
    """Request to analyze content"""
    url: Optional[str] = None
    text: Optional[str] = None
    platform_hint: Optional[str] = None


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint"""
    success: bool
    data: Optional[SafetyAnalysisResult] = None
    error: Optional[str] = None
    cached: bool = False


# Global instances
pipeline: Optional[IngestionPipeline] = None
gemini_service: Optional[GeminiService] = None
result_cache: Optional[ResultCache] = None
metrics: Optional[MetricsTracker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global pipeline, gemini_service, result_cache, metrics
    
    print("Starting SafetyCheck API...")
    
    # Initialize media cache
    media_cache_dir = Path(os.getenv("MEDIA_CACHE_DIR", "./media_cache"))
    media_cache_dir.mkdir(exist_ok=True)
    
    pipeline = IngestionPipeline(media_cache_dir=media_cache_dir)
    
    # Initialize Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    gemini_service = GeminiService(api_key=gemini_api_key)
    
    # Initialize cache
    cache_type = os.getenv("CACHE_TYPE", "memory")
    if cache_type == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        result_cache = ResultCache(backend="redis", redis_url=redis_url)
    else:
        result_cache = ResultCache(backend="memory")
    
    # Initialize metrics
    metrics = MetricsTracker(
        hourly_request_limit=int(os.getenv("HOURLY_REQUEST_LIMIT", "100")),
        daily_request_limit=int(os.getenv("DAILY_REQUEST_LIMIT", "1000")),
    )
    
    # Register adapters
    reddit_adapter = RedditAdapter({
        "client_id": os.getenv("REDDIT_CLIENT_ID", "test"),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "test"),
    })
    adapter_registry.register(reddit_adapter)
    
    twitter_adapter = TwitterAdapter({
        "bearer_token": os.getenv("TWITTER_BEARER_TOKEN", "test"),
    })
    adapter_registry.register(twitter_adapter)
    
    print(f"Registered {len(adapter_registry.adapters)} adapters")
    print(f"Cache: {cache_type}")
    print("SafetyCheck API ready")
    
    yield
    
    # Cleanup
    print("Shutting down...")
    await pipeline.cleanup()
    await result_cache.close()
    print("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="SafetyCheck API",
    description="AI-powered safety analysis for social media content",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(time.time() - start)
    return response


@app.get("/")
async def root():
    return {"service": "SafetyCheck API", "version": "1.0.0", "status": "online"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "pipeline": "ok" if pipeline else "not_initialized",
            "gemini": "ok" if gemini_service else "not_initialized",
            "cache": "ok" if result_cache else "not_initialized",
        },
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_content(request: AnalysisRequest):
    """Analyze content for safety risks."""
    start_time = time.time()
    
    try:
        if not request.url and not request.text:
            raise HTTPException(400, "Either 'url' or 'text' required")
        
        # Generate cache key
        cache_key = result_cache.generate_cache_key(
            url=request.url,
            text=request.text,
        )
        
        # Check cache
        cached_result = await result_cache.get(cache_key)
        if cached_result:
            metrics.record_cache_hit()
            return AnalysisResponse(success=True, data=cached_result, cached=True)
        
        metrics.record_cache_miss()
        
        # Check rate limits
        if not metrics.check_rate_limit():
            raise HTTPException(429, "Rate limit exceeded")
        
        # Ingest content
        if request.url:
            post = await pipeline.ingest_from_url(
                url=request.url,
                platform_hint=request.platform_hint,
            )
        else:
            post = await pipeline.ingest_from_text(
                text=request.text,
                platform_hint=request.platform_hint,
            )
        
        # Analyze
        result = await gemini_service.analyze(post)
        
        # Cache result
        await result_cache.set(cache_key, result)
        
        # Record metrics
        latency = time.time() - start_time
        metrics.record_request(latency=latency, tokens=len(post.post_text) // 4)
        
        return AnalysisResponse(success=True, data=result, cached=False)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.get("/api/metrics")
async def get_metrics():
    """Get service metrics."""
    return {
        "cache": metrics.get_cache_stats(),
        "requests": metrics.get_request_stats(),
        "rate_limits": metrics.get_rate_limit_stats(),
        "gemini": gemini_service.get_metrics() if gemini_service else {},
    }


@app.delete("/api/cache")
async def clear_cache():
    """Clear result cache."""
    await result_cache.clear()
    return {"message": "Cache cleared"}


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
