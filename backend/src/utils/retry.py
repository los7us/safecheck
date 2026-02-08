"""
Retry Utilities

Exponential backoff retry logic for transient failures.
"""

import asyncio
from typing import Callable, TypeVar, Optional
from functools import wraps
import random

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return delay


def is_retryable_error(error: Exception) -> bool:
    """Determine if an error is retryable."""
    error_str = str(error).lower()
    
    retryable_keywords = [
        "timeout", "timed out", "connection", "rate limit",
        "429", "503", "500", "502", "504", "temporarily unavailable",
    ]
    
    return any(keyword in error_str for keyword in retryable_keywords)


async def async_retry(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """Retry an async function with exponential backoff."""
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        
        except Exception as e:
            last_exception = e
            
            if attempt >= config.max_attempts - 1:
                break
            
            if not is_retryable_error(e):
                raise
            
            delay = config.calculate_delay(attempt)
            print(f"Retry {attempt + 1}/{config.max_attempts} after {delay:.2f}s: {e}")
            await asyncio.sleep(delay)
    
    raise last_exception


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator for async functions with retry logic."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await async_retry(func, *args, config=config, **kwargs)
        return wrapper
    return decorator
