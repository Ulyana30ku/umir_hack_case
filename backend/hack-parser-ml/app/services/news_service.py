"""News service for news search and deduplication."""

import asyncio
from typing import List, Optional, Tuple, Dict, Any
import re
from collections import defaultdict

from app.schemas.news import NewsItem, NewsSearchResult
from app.schemas.query import NewsTask
from app.integrations.news.base import BaseNewsSource
from app.integrations.news.rss_news import get_rss_news_source, RSSNewsSource
from app.services.ranking_service import rank_news
from app.core.logging import get_logger
from app.core.config import settings
from app.core.cache import get_cache, make_news_search_key
from app.utils.retry import retry_with_backoff, get_rate_limiter

logger = get_logger(__name__)


class NewsService:
    """Service for news search, deduplication, and ranking with external sources only."""
    
    def __init__(self):
        """Initialize news service with real RSS sources."""
        self._news_sources: List[BaseNewsSource] = []
        self._cache = get_cache(settings.cache_ttl_seconds)
        self._rate_limiter = get_rate_limiter()
        self._init_news_sources()
    
    def _init_news_sources(self):
        """Initialize news sources - real RSS feeds only."""
        # Use multiple RSS sources for failover
        logger.info("Initializing RSS News Sources (real sources only)")
        self._news_sources = [
            get_rss_news_source(),
        ]
    
    async def search_news(
        self,
        task: NewsTask,
    ) -> Tuple[List[NewsItem], Dict[str, Any]]:
        """
        Search for news matching the task with cache + retry + failover.
        
        Args:
            task: News search task
            
        Returns:
            Tuple of (news items, metadata dict)
        """
        logger.info(f"Searching news for task: {task}")
        
        metadata = {
            "sources_tried": [],
            "cache_hit": False,
            "total_retries": 0,
            "failover_used": False,
            "unavailable_sources": [],
        }
        
        # Try cache first if enabled
        if settings.cache_enabled:
            cache_key = make_news_search_key(task.topic, task.limit)
            cached_result = await self._cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for news search")
                metadata["cache_hit"] = True
                return cached_result, metadata
        
        # Try each news source with failover
        all_news = []
        
        for source in self._news_sources:
            metadata["sources_tried"].append(source.name)
            
            retry_result = await retry_with_backoff(
                source.search_news,
                task,
                max_retries=settings.max_retries,
                base_delay=settings.retry_base_delay,
                max_delay=settings.retry_max_delay,
                rate_limiter=self._rate_limiter,
                source_name=source.name,
            )
            
            if retry_result.success:
                result = retry_result.result
                all_news.extend(result.news)
                metadata["total_retries"] += retry_result.attempts - 1
                logger.info(f"Got {len(result.news)} news from {source.name}")
                break  # Success, no need to failover
            else:
                logger.warning(f"News source {source.name} failed: {retry_result.error}")
                metadata["unavailable_sources"].append(source.name)
                metadata["total_retries"] += retry_result.attempts
                # Continue to next source (failover)
                metadata["failover_used"] = True
        
        if not all_news:
            logger.warning("All news sources failed")
            return [], metadata
        
        # Deduplicate
        deduplicated = self.deduplicate_news(all_news)
        
        # Rank
        ranked = rank_news(deduplicated, task.limit)
        
        logger.info(f"Found {len(ranked)} news items after dedup and rank")
        
        # Cache the result if enabled
        if settings.cache_enabled:
            await self._cache.set(cache_key, ranked, source="rss_news")
        
        return ranked, metadata
    
    def deduplicate_news(
        self,
        news_items: List[NewsItem],
        similarity_threshold: float = 0.8,
    ) -> List[NewsItem]:
        """
        Deduplicate news items based on title similarity.
        
        Args:
            news_items: List of news items
            similarity_threshold: Threshold for considering items duplicates
            
        Returns:
            Deduplicated list of news items
        """
        if not news_items:
            return []
        
        # Group items by normalized title
        groups = defaultdict(list)
        
        for item in news_items:
            normalized = self._normalize_title(item.title)
            groups[normalized].append(item)
        
        # Keep the best item from each group
        deduplicated = []
        for normalized_title, items in groups.items():
            # Sort by relevance score
            best = sorted(items, key=lambda n: -n.relevance_score)[0]
            
            # Mark duplicates
            if len(items) > 1:
                best.duplicate_group = normalized_title
            
            deduplicated.append(best)
        
        logger.info(f"Deduplicated {len(news_items)} items to {len(deduplicated)}")
        return deduplicated
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        # Convert to lowercase
        normalized = title.lower()
        
        # Remove punctuation
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    async def get_news(
        self,
        task: NewsTask,
        deduplicate: bool = True,
    ) -> Tuple[List[NewsItem], Dict[str, Any]]:
        """
        Get news with optional deduplication and ranking.
        
        Args:
            task: News search task
            deduplicate: Whether to deduplicate results
            
        Returns:
            Tuple of (processed news items, metadata dict)
        """
        news_items, metadata = await self.search_news(task)
        return news_items, metadata


# Singleton instance
_news_service: Optional[NewsService] = None


def get_news_service() -> NewsService:
    """Get the news service singleton."""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service


async def search_news(task: NewsTask) -> Tuple[List[NewsItem], Dict[str, Any]]:
    """Search and process news."""
    service = get_news_service()
    return await service.search_news(task)
