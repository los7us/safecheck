"""
Metrics Tracker

Tracks requests, cache hits, token usage, and rate limits.
"""

from typing import Dict
from datetime import datetime, timedelta
from collections import defaultdict
import threading


class MetricsTracker:
    """Thread-safe metrics tracker for monitoring and cost control."""
    
    def __init__(
        self,
        hourly_request_limit: int = 100,
        daily_request_limit: int = 1000,
        daily_token_limit: int = 1_000_000,
    ):
        self.lock = threading.Lock()
        
        # Limits
        self.hourly_request_limit = hourly_request_limit
        self.daily_request_limit = daily_request_limit
        self.daily_token_limit = daily_token_limit
        
        # Counters
        self.total_requests = 0
        self.total_cache_hits = 0
        self.total_cache_misses = 0
        self.total_tokens = 0
        self.total_latency = 0.0
        
        # Time-windowed counters
        self.hourly_requests: Dict[datetime, int] = defaultdict(int)
        self.daily_requests: Dict[datetime, int] = defaultdict(int)
        self.daily_tokens: Dict[datetime, int] = defaultdict(int)
        
        # Current period keys
        self.current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        self.current_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _update_time_windows(self):
        """Update time window keys"""
        now = datetime.utcnow()
        
        new_hour = now.replace(minute=0, second=0, microsecond=0)
        if new_hour > self.current_hour:
            self.current_hour = new_hour
            cutoff = new_hour - timedelta(hours=24)
            self.hourly_requests = defaultdict(int, {
                k: v for k, v in self.hourly_requests.items() if k >= cutoff
            })
        
        new_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if new_day > self.current_day:
            self.current_day = new_day
            cutoff = new_day - timedelta(days=30)
            self.daily_requests = defaultdict(int, {
                k: v for k, v in self.daily_requests.items() if k >= cutoff
            })
            self.daily_tokens = defaultdict(int, {
                k: v for k, v in self.daily_tokens.items() if k >= cutoff
            })
    
    def record_request(self, latency: float, tokens: int):
        """Record a completed request."""
        with self.lock:
            self._update_time_windows()
            
            self.total_requests += 1
            self.total_latency += latency
            self.total_tokens += tokens
            
            self.hourly_requests[self.current_hour] += 1
            self.daily_requests[self.current_day] += 1
            self.daily_tokens[self.current_day] += tokens
    
    def record_cache_hit(self):
        with self.lock:
            self.total_cache_hits += 1
    
    def record_cache_miss(self):
        with self.lock:
            self.total_cache_misses += 1
    
    def check_rate_limit(self) -> bool:
        """Check if request is within rate limits."""
        with self.lock:
            self._update_time_windows()
            
            if self.hourly_requests[self.current_hour] >= self.hourly_request_limit:
                return False
            
            if self.daily_requests[self.current_day] >= self.daily_request_limit:
                return False
            
            if self.daily_tokens[self.current_day] >= self.daily_token_limit:
                return False
            
            return True
    
    def get_cache_stats(self) -> dict:
        with self.lock:
            total = self.total_cache_hits + self.total_cache_misses
            hit_rate = self.total_cache_hits / total if total > 0 else 0.0
            
            return {
                "total_hits": self.total_cache_hits,
                "total_misses": self.total_cache_misses,
                "hit_rate": hit_rate,
            }
    
    def get_request_stats(self) -> dict:
        with self.lock:
            avg_latency = self.total_latency / max(self.total_requests, 1)
            
            return {
                "total_requests": self.total_requests,
                "avg_latency_seconds": avg_latency,
                "total_tokens": self.total_tokens,
            }
    
    def get_rate_limit_stats(self) -> dict:
        with self.lock:
            self._update_time_windows()
            
            hourly_count = self.hourly_requests[self.current_hour]
            daily_count = self.daily_requests[self.current_day]
            daily_token_count = self.daily_tokens[self.current_day]
            
            return {
                "hourly": {
                    "count": hourly_count,
                    "limit": self.hourly_request_limit,
                    "remaining": max(0, self.hourly_request_limit - hourly_count),
                },
                "daily": {
                    "requests": {
                        "count": daily_count,
                        "limit": self.daily_request_limit,
                        "remaining": max(0, self.daily_request_limit - daily_count),
                    },
                    "tokens": {
                        "count": daily_token_count,
                        "limit": self.daily_token_limit,
                        "remaining": max(0, self.daily_token_limit - daily_token_count),
                    },
                },
            }
    
    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "gemini-1.5-pro"
    ) -> float:
        """Estimate cost for Gemini API call."""
        pricing = {
            "gemini-1.5-pro": {"input": 0.35 / 1_000_000, "output": 1.05 / 1_000_000},
            "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
        }
        
        rates = pricing.get(model, pricing["gemini-1.5-pro"])
        return (input_tokens * rates["input"]) + (output_tokens * rates["output"])
