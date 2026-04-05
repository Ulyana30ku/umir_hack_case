"""Product service for product search and processing."""

import asyncio
from typing import List, Optional, Tuple, Dict, Any

from app.schemas.product import ProductCandidate, ProductSearchResult
from app.schemas.query import ProductTask
from app.integrations.marketplaces.base import BaseMarketplace
from app.integrations.marketplaces.yandex_market import get_yandex_marketplace
from app.services.validation_service import validate_products
from app.services.ranking_service import rank_products_extended
from app.core.logging import get_logger
from app.core.config import settings
from app.core.cache import get_cache, make_product_search_key
from app.utils.retry import retry_with_backoff, get_rate_limiter, RetryResult
from app.schemas.trace import AgentTraceStep
from datetime import datetime

logger = get_logger(__name__)


class ProductService:
    """Service for product search, validation, and ranking with external sources only."""
    
    def __init__(self):
        """Initialize product service with real marketplace."""
        self._marketplace: Optional[BaseMarketplace] = None
        self._cache = get_cache(settings.cache_ttl_seconds)
        self._rate_limiter = get_rate_limiter()
    
    def _get_marketplace(self) -> BaseMarketplace:
        """Get or create marketplace instance."""
        if self._marketplace is None:
            # Use real marketplace only
            logger.info("Using Yandex Market (real sources only)")
            self._marketplace = get_yandex_marketplace()
        return self._marketplace
    
    async def search_products(
        self,
        task: ProductTask,
        limit: int = 20,
    ) -> Tuple[List[ProductCandidate], Dict[str, Any]]:
        """
        Search for products matching the task with cache + retry.
        
        Args:
            task: Product search task
            limit: Maximum number of results
            
        Returns:
            Tuple of (product candidates, metadata dict)
        """
        logger.info(f"Searching products for task: {task}")
        
        metadata = {
            "source_used": "Yandex Market",
            "cache_hit": False,
            "retry_count": 0,
            "failover_used": False,
            "unavailable_sources": [],
        }
        
        # Try cache first if enabled
        if settings.cache_enabled:
            cache_key = make_product_search_key(
                task.brand, task.model, task.memory_gb
            )
            cached_result = await self._cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for product search")
                metadata["cache_hit"] = True
                return cached_result, metadata
        
        # Search using marketplace with retry
        marketplace = self._get_marketplace()
        
        retry_result = await retry_with_backoff(
            marketplace.search_products,
            task,
            limit,
            max_retries=settings.max_retries,
            base_delay=settings.retry_base_delay,
            max_delay=settings.retry_max_delay,
            rate_limiter=self._rate_limiter,
            source_name=marketplace.name,
        )
        
        if not retry_result.success:
            logger.warning(f"Product search failed: {retry_result.error}")
            metadata["unavailable_sources"].append(marketplace.name)
            return [], metadata
        
        metadata["retry_count"] = retry_result.attempts - 1
        result = retry_result.result
        
        logger.info(f"Found {len(result.products)} products")
        
        # Cache the result if enabled
        if settings.cache_enabled:
            await self._cache.set(cache_key, result.products, source=marketplace.name)
        
        return result.products, metadata
    
    async def get_products(
        self,
        task: ProductTask,
    ) -> Tuple[
        Optional[ProductCandidate],
        List[ProductCandidate],
        List[ProductCandidate],
        Dict[str, Any],
    ]:
        """
        Get processed products: search, validate, rank.
        
        Args:
            task: Product search task
            
        Returns:
            Tuple of (selected_product, alternatives, rejected_products, metadata)
        """
        # Step 1: Search products
        products, metadata = await self.search_products(task)
        
        if not products:
            logger.warning("No products found")
            return None, [], [], metadata
        
        # Step 2: Validate products
        validated = validate_products(products, task)
        
        # Step 3: Rank products (using extended version to get rejected)
        selected, alternatives, rejected = rank_products_extended(validated, task)
        
        return selected, alternatives, rejected, metadata


# Singleton instance
_product_service: Optional[ProductService] = None


def get_product_service() -> ProductService:
    """Get the product service singleton."""
    global _product_service
    if _product_service is None:
        _product_service = ProductService()
    return _product_service


async def search_products(task: ProductTask) -> Tuple[List[ProductCandidate], Dict[str, Any]]:
    """Search products."""
    service = get_product_service()
    return await service.search_products(task)


async def get_products(
    task: ProductTask,
) -> Tuple[
    Optional[ProductCandidate],
    List[ProductCandidate],
    List[ProductCandidate],
    Dict[str, Any],
]:
    """Get processed products."""
    service = get_product_service()
    return await service.get_products(task)
