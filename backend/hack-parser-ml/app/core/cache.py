"""Caching layer for external source results."""

import asyncio
import hashlib
import json
import time
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:

    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    source: str  # Source that generated this data
    
    def is_expired(self) -> bool:

        return datetime.now() > self.expires_at
    
    def age_seconds(self) -> float:

        return (datetime.now() - self.created_at).total_seconds()


class CacheStore:

    
    def __init__(self, default_ttl: int = 3600):
      
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:


        key_parts = [prefix]
        for arg in args:
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        
        key_string = "|".join(key_parts)

        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:

        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                logger.debug(f"Cache expired for key: {key[:20]}...")
                return None
            
            logger.debug(f"Cache hit for key: {key[:20]}... (age: {entry.age_seconds():.1f}s)")
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        source: str = "unknown",
    ) -> None:

        ttl = ttl or self._default_ttl
        
        async with self._lock:
            now = datetime.now()
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl),
                source=source,
            )
            logger.debug(f"Cached key: {key[:20]}... (ttl: {ttl}s, source: {source})")
    
    async def delete(self, key: str) -> bool:

        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> int:

        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} cache entries")
            return count
    
    async def cleanup_expired(self) -> int:

        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:

        total = len(self._cache)
        expired = sum(1 for e in self._cache.values() if e.is_expired())
        
        # Count by source
        by_source: Dict[str, int] = {}
        for entry in self._cache.values():
            if not entry.is_expired():
                by_source[entry.source] = by_source.get(entry.source, 0) + 1
        
        return {
            "total_entries": total,
            "expired_entries": expired,
            "by_source": by_source,
        }



_cache: Optional[CacheStore] = None


def get_cache(default_ttl: int = 3600) -> CacheStore:

    global _cache
    if _cache is None:
        _cache = CacheStore(default_ttl)
    return _cache




def make_product_search_key(brand: Optional[str], model: Optional[str], memory_gb: Optional[int]) -> str:

    return f"product_search|brand={brand or ''}|model={model or ''}|memory={memory_gb or 0}"


def make_product_page_key(product_id: str) -> str:

    return f"product_page|id={product_id}"


def make_news_search_key(topic: str, limit: int) -> str:

    return f"news_search|topic={topic}|limit={limit}"


def make_news_page_key(news_id: str) -> str:

    return f"news_page|id={news_id}"