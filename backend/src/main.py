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

from src.core.schemas import SafetyAnalysisResult, AnalysisRequest, AnalysisResponse
from src.services.ingestion_pipeline import IngestionPipeline
from src.services.gemini_service import GeminiService, GeminiRateLimitError
from src.adapters.registry import adapter_registry
from src.adapters.reddit_adapter import RedditAdapter
from src.adapters.twitter_adapter import TwitterAdapter
from src.cache.result_cache import ResultCache
from src.monitoring.metrics import MetricsTracker
from starlette.middleware.base import BaseHTTPMiddleware

load_dotenv()

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Limit request body size"""
    
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get('content-length')
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={"success": False, "error": f"Request body too large (max {self.max_size} bytes)"}
            )
        
        return await call_next(request)


# Global instances
pipeline: Optional[IngestionPipeline] = None
gemini_service: Optional[GeminiService] = None
result_cache: Optional[ResultCache] = None
metrics: Optional[MetricsTracker] = None


from src.utils.logging import setup_logging

# Initialize logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global pipeline, gemini_service, result_cache, metrics
    
    logger.info("Starting SafetyCheck API...")
    
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
    
    logger.info(f"Registered {len(adapter_registry.list_platforms())} adapters")
    logger.info(f"Cache: {cache_type}")
    
    # Initialize image upload handler
    global image_upload_handler
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(parents=True, exist_ok=True)
    from src.services.image_upload_handler import ImageUploadHandler
    image_upload_handler = ImageUploadHandler(
        upload_dir=upload_dir,
        max_size_mb=int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
    )
    logger.info(f"Image upload handler initialized (dir: {upload_dir})")
    
    logger.info("SafetyCheck API ready")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    await pipeline.cleanup()
    await result_cache.close()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="SafetyCheck API",
    description="AI-powered safety analysis for social media content",
    version="1.0.0",
    lifespan=lifespan,
)

# Request Size Limit (15MB to support image uploads)
app.add_middleware(RequestSizeLimitMiddleware, max_size=15 * 1024 * 1024)

# Abuse Prevention
from src.middleware.abuse_prevention import AbusePreventionMiddleware
app.add_middleware(AbusePreventionMiddleware)

# CORS
# Explicitly whitelist origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"], # Allow all headers for now or restrict to Content-Type, Authorization, X-API-Key
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


from src.middleware.auth import verify_api_key
from src.middleware.rate_limit import rate_limiter
from fastapi import Security, Depends


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_content(
    request: AnalysisRequest,
    api_key: str = Security(verify_api_key)
):
    """Analyze content for safety risks."""
    # Check per-key rate limit
    allowed, reason = rate_limiter.check_rate_limit(api_key)
    if not allowed:
        raise HTTPException(429, f"Rate limit exceeded: {reason}")
        
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
            )
        else:
            post = await pipeline.ingest_from_text(
                raw_text=request.text,
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
    except GeminiRateLimitError as e:
        raise HTTPException(429, f"AI Service Rate Limit: {str(e)}")
    except Exception as e:
        print(f"Analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")


# Image upload imports and handler
from fastapi import UploadFile, File, Form
from src.services.image_upload_handler import ImageUploadHandler, ImageUploadException

# Global image upload handler (initialized in lifespan)
image_upload_handler: Optional[ImageUploadHandler] = None


@app.post("/api/analyze/image", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    api_key: str = Security(verify_api_key)
):
    """
    Analyze an uploaded screenshot/image using Gemini Vision.
    
    VISION-ENABLED: Sends image directly to Gemini Vision API
    for multimodal analysis (text + image together).
    
    Args:
        file: Uploaded image file (PNG, JPG, etc.)
        context: Optional user-provided context about the image
    
    Returns:
        AnalysisResponse with SafetyAnalysisResult
    """
    # Rate limit check
    allowed, reason = rate_limiter.check_rate_limit(api_key)
    if not allowed:
        raise HTTPException(429, f"Rate limit exceeded: {reason}")
    
    start_time = time.time()
    
    try:
        # Read file content
        content = await file.read()
        
        # Process upload (returns post AND image path for vision)
        post, image_path = await image_upload_handler.process_upload(
            file_content=content,
            filename=file.filename or "upload.png",
            user_context=context,
        )
        
        # Analyze with Gemini VISION (sends actual image)
        result = await gemini_service.analyze(post, image_path=image_path)
        
        # Record metrics
        latency = time.time() - start_time
        metrics.record_request(latency=latency, tokens=len(post.post_text) // 4)
        
        logger.info(f"Vision analysis completed in {latency:.2f}s")
        
        return AnalysisResponse(success=True, data=result, cached=False)
    
    except ImageUploadException as e:
        raise HTTPException(400, f"Image upload failed: {str(e)}")
    except GeminiRateLimitError as e:
        raise HTTPException(429, f"AI Service Rate Limit: {str(e)}")
    except Exception as e:
        logger.error(f"Image analysis error: {e}", exc_info=True)
        raise HTTPException(500, f"Image analysis failed: {str(e)}")

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


from src.middleware.security_headers import SecurityHeadersMiddleware

# Security Headers
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(Exception)
async def global_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    CRITICAL: Never expose internal errors to users.
    """
    # Log full error internally (in production logs)
    logger.error(f"INTERNAL ERROR: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "error": "An internal error occurred. Please try again later."
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
