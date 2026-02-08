"""
Per-API-Key Rate Limiting

Prevent abuse by tracking requests per key.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import threading

class APIKeyRateLimiter:
    """Rate limiter per API key"""
    
    def __init__(
        self,
        requests_per_hour: int = 100,
        requests_per_day: int = 1000,
    ):
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        
        # Track requests: {api_key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = threading.Lock()
    
    def check_rate_limit(self, api_key: str) -> Tuple[bool, str]:
        """
        Check if API key is within rate limits.
        
        Returns:
            (allowed, reason)
        """
        with self.lock:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Clean old entries
            self.requests[api_key] = [
                (ts, count) for ts, count in self.requests[api_key]
                if ts > day_ago
            ]
            
            # Count requests
            hourly = sum(
                count for ts, count in self.requests[api_key]
                if ts > hour_ago
            )
            daily = sum(count for ts, count in self.requests[api_key])
            
            # Check limits
            if hourly >= self.requests_per_hour:
                return False, f"Hourly limit exceeded ({hourly}/{self.requests_per_hour})"
            
            if daily >= self.requests_per_day:
                return False, f"Daily limit exceeded ({daily}/{self.requests_per_day})"
            
            # Record request
            self.requests[api_key].append((now, 1))
            
            return True, "OK"

# Global rate limiter instance
rate_limiter = APIKeyRateLimiter()
