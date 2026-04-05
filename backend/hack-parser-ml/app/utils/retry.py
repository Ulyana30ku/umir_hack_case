"""Retry and rate limiting utilities for external sources."""

import asyncio
import time
from typing import Any, Callable, Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter for API calls per source."""
    
    def __init__(self, calls_per_second: float = 2.0, window_seconds: float = 1.0):
        """Initialize rate limiter.
        
        Args:
            calls_per_second: Maximum calls per second
            window_seconds: Time window for rate limiting
        """
        self._calls_per_second = calls_per_second
        self._window_seconds = window_seconds
        self._last_call_time: Dict[str, datetime] = {}
        self._call_count: Dict[str, int] = {}
        self._window_start: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def acquire(self, source: str) -> None:
        """Acquire permission to make a call.
        
        Args:
            source: Source identifier
        """
        async with self._lock:
            now = datetime.now()
            
            # Initialize if first call
            if source not in self._window_start:
                self._window_start[source] = now
                self._call_count[source] = 0
            
            # Check if we need to reset the window
            window_elapsed = (now - self._window_start[source]).total_seconds()
            if window_elapsed >= self._window_seconds:
                # Reset window
                self._window_start[source] = now
                self._call_count[source] = 0
            
            # Check if we've hit the limit
            if self._call_count[source] >= self._calls_per_second:
                # Calculate wait time
                wait_time = self._window_seconds - window_elapsed
                if wait_time > 0:
                    logger.debug(f"Rate limiting {source}, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    # Reset after waiting
                    self._window_start[source] = datetime.now()
                    self._call_count[source] = 0
            
            # Increment call count
            self._call_count[source] += 1
            self._last_call_time[source] = now


class RetryError(Exception):
    """Exception for retry failures."""
    def __init__(self, message: str, attempts: int, last_error: Optional[str] = None):
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


@dataclass
class RetryResult:
    """Result of a retry operation."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    attempts: int = 0
    total_time_ms: float = 0.0
    cached: bool = False
    

async def retry_with_backoff(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retry_on_errors: tuple = (Exception,),
    rate_limiter: Optional[RateLimiter] = None,
    source_name: str = "unknown",
    **kwargs,
) -> RetryResult:
    """Execute function with exponential backoff retry.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        retry_on_errors: Tuple of error types to retry on
        rate_limiter: Optional rate limiter
        source_name: Name of the source for rate limiting
        **kwargs: Keyword arguments for the function
        
    Returns:
        RetryResult with success status and result/error
    """
    start_time = time.time()
    last_error = None
    
    # Apply rate limiting if provided
    if rate_limiter:
        await rate_limiter.acquire(source_name)
    
    for attempt in range(max_retries + 1):
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"{source_name}: attempt {attempt + 1} succeeded in {elapsed_ms:.1f}ms")
            
            return RetryResult(
                success=True,
                result=result,
                attempts=attempt + 1,
                total_time_ms=elapsed_ms,
            )
            
        except retry_on_errors as e:
            last_error = str(e)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Don't retry on last attempt
            if attempt >= max_retries:
                logger.warning(f"{source_name}: all {max_retries + 1} attempts failed: {last_error}")
                return RetryResult(
                    success=False,
                    error=last_error,
                    attempts=attempt + 1,
                    total_time_ms=elapsed_ms,
                )
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            
            # Add jitter (10-20%)
            import random
            jitter = delay * 0.1 * random.random()
            total_delay = delay + jitter
            
            logger.debug(f"{source_name}: attempt {attempt + 1} failed: {last_error}, retrying in {total_delay:.2f}s")
            await asyncio.sleep(total_delay)
    
    # Should not reach here, but just in case
    return RetryResult(
        success=False,
        error=last_error or "Unknown error",
        attempts=max_retries + 1,
        total_time_ms=(time.time() - start_time) * 1000,
    )


async def retry_with_failover(
    sources: List[Callable],
    *args,
    max_retries_per_source: int = 2,
    rate_limiter: Optional[RateLimiter] = None,
    **kwargs,
) -> RetryResult:
    """Execute function with failover across multiple sources.
    
    Args:
        sources: List of async functions to try (in order of priority)
        *args: Positional arguments for the function
        max_retries_per_source: Maximum retries per source
        rate_limiter: Optional rate limiter
        **kwargs: Keyword arguments for the function
        
    Returns:
        RetryResult from first successful source
    """
    errors = []
    
    for i, source_func in enumerate(sources):
        source_name = getattr(source_func, '__name__', f"source_{i}")
        
        result = await retry_with_backoff(
            source_func,
            *args,
            max_retries=max_retries_per_source,
            rate_limiter=rate_limiter,
            source_name=source_name,
            **kwargs,
        )
        
        if result.success:
            result.result.failover_source = source_name
            return result
        
        errors.append(f"{source_name}: {result.error}")
    
    # All sources failed
    return RetryResult(
        success=False,
        error=f"All sources failed: {'; '.join(errors)}",
        attempts=len(sources) * (max_retries_per_source + 1),
    )


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(
            calls_per_second=settings.rate_limit_per_source,
            window_seconds=settings.rate_limit_window,
        )
    return _rate_limiter