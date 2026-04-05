"""Cache service with retry logic."""

import asyncio
import hashlib
import json
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps

from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """Simple in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict = {}
        self._default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry["expires_at"] < datetime.now():
            # Expired
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit: {key}")
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        ttl = ttl or self._default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": datetime.now(),
        }
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")
    
    def delete(self, key: str):
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry["expires_at"] < now
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments."""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


async def with_retry(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Execute function with retry logic.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Result of the function
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_retries + 1):
        try:
            result = await func()
            if attempt > 0:
                logger.info(f"Succeeded after {attempt} retries")
            return result
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {current_delay}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception


# Decorator for caching async functions
def cached(ttl: int = 300):
    """Decorator to cache async function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache from arguments
            key = cache_key(func.__name__, *args, **kwargs)
            
            # Get cache service
            cache = get_cache_service()
            
            # Try cache first
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get cache service singleton."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service