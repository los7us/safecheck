
from collections import defaultdict
from datetime import datetime, timedelta
import hashlib
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class AbuseDetector:
    """Detect and prevent abuse patterns"""
    
    def __init__(self):
        # Track requests per IP
        self.ip_requests = defaultdict(list)
        
        # Track unique content per IP
        self.ip_content_hashes = defaultdict(set)
    
    def check_abuse(self, ip: str, content: str) -> bool:
        """
        Check for abuse patterns.
        Returns True if abuse detected.
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.ip_requests[ip] = [
            ts for ts in self.ip_requests[ip]
            if ts > minute_ago
        ]
        
        # Check request rate (max 60/minute per IP)
        if len(self.ip_requests[ip]) >= 60:
            logger.warning(f"Abuse detected: Too many requests from IP {ip}")
            return True
        
        # Record request
        self.ip_requests[ip].append(now)
        
        # Check for cache bypass attempts (same IP, different content)
        if content:
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            # If same content, it's fine (cache hit likely)
            if content_hash in self.ip_content_hashes[ip]:
                return False
            
            self.ip_content_hashes[ip].add(content_hash)
            
            # If same IP has >50 unique content hashes in 1 hour, flag as abuse
            # (Note: This simple impl doesn't clean up hashes, production needs expiry)
            if len(self.ip_content_hashes[ip]) > 50:
                logger.warning(f"Abuse detected: Cache bypass attempt from IP {ip}")
                return True
        
        return False

# Global instance
abuse_detector = AbuseDetector()

from fastapi.responses import JSONResponse

class AbusePreventionMiddleware(BaseHTTPMiddleware):
    """Middleware to check abuse patterns"""
    
    async def dispatch(self, request: Request, call_next):
        # We need request body to check content hash, but consuming stream in middleware is tricky.
        # For simplicity, we'll check IP rate limits here. Content check is better in endpoint.
        
        ip = request.client.host if request.client else "unknown"
        
        # Check abuse (content is empty here for middleware simplicity)
        if abuse_detector.check_abuse(ip, ""):
             logger.warning(f"Abuse blocked from IP {ip}")
             return JSONResponse(
                 status_code=429, 
                 content={"success": False, "error": "Too many requests or abuse detected"}
             )
             
        return await call_next(request)
