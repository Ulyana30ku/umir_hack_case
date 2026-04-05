"""Ranking service for products and news."""

from typing import List, Optional, Tuple
from datetime import datetime

from app.schemas.product import ProductCandidate
from app.schemas.news import NewsItem
from app.schemas.query import ProductTask
from app.schemas.response import SourceScore
from app.core.logging import get_logger

logger = get_logger(__name__)

# Source reliability scores (could be loaded from config)
SOURCE_SCORES = {
    "Demo Marketplace": 0.5,  # Lower score for mock data
    "Yandex Market": 0.9,
    "Wildberries": 0.85,
    "OZON": 0.85,
    "SberMegaMarket": 0.8,
    "TechNews": 0.7,
    "iXBT": 0.85,
    "3DNews": 0.8,
    "Habr": 0.9,
}


class RankingService:
    """Service for ranking products and news."""
    
    def rank_products(
        self,
        candidates: List[ProductCandidate],
        task: ProductTask,
        include_rejected: bool = False,
    ) -> Tuple[Optional[ProductCandidate], List[ProductCandidate]]:
        """
        Rank product candidates and select the best one.
        
        Ranking criteria:
        1. Full constraint match (all constraints satisfied)
        2. Price (if cheapest requested)
        3. Confidence
        4. Rating
        
        Args:
            candidates: List of validated candidates
            task: Product search task
            include_rejected: If True, return rejected products separately
            
        Returns:
            Tuple of (selected_product, alternatives) or (selected_product, alternatives, rejected_products) if include_rejected=True
        """
        if not candidates:
            logger.warning("No candidates to rank")
            if include_rejected:
                return None, [], []
            return None, []
        
        # Separate valid and invalid candidates
        valid = [c for c in candidates if not c.rejection_reason]
        invalid = [c for c in candidates if c.rejection_reason]
        
        if not valid:
            logger.warning("No valid candidates after validation")
            if include_rejected:
                return None, [], invalid
            return None, []
        
        # Sort valid candidates
        # Primary: number of matched constraints (more is better)
        # Secondary: price (ascending if cheapest requested)
        # Tertiary: confidence
        
        def sort_key(p: ProductCandidate):
            # Handle None prices safely
            price = p.price if p.price else float('inf')
            if task.sort_by == "price_asc":
                price_order = price
            else:
                price_order = -price
            
            return (
                -len(p.matched_constraints),  # More constraints matched
                price_order,  # Price order
                -(p.rating or 0),  # Rating
                -(p.confidence or 0),  # Confidence
            )
        
        sorted_candidates = sorted(valid, key=sort_key)
        
        selected = sorted_candidates[0]
        alternatives = sorted_candidates[1:5]  # Top 4 alternatives
        
        logger.info(f"Ranked products: selected {selected.id}, {len(alternatives)} alternatives, {len(invalid)} rejected")
        
        if include_rejected:
            return selected, alternatives, invalid
        return selected, alternatives
    
    def rank_products_extended(
        self,
        candidates: List[ProductCandidate],
        task: ProductTask,
    ) -> Tuple[Optional[ProductCandidate], List[ProductCandidate], List[ProductCandidate]]:
        """
        Rank products and return rejected products.
        
        Args:
            candidates: List of validated candidates
            task: Product search task
            
        Returns:
            Tuple of (selected_product, alternatives, rejected_products)
        """
        return self.rank_products(candidates, task, include_rejected=True)
    
    def rank_news(
        self,
        news_items: List[NewsItem],
        limit: int = 5,
    ) -> List[NewsItem]:
        """
        Rank news items by relevance.
        
        Args:
            news_items: List of news items
            limit: Maximum number of results
            
        Returns:
            Ranked list of news items
        """
        if not news_items:
            return []
        
        # Sort by relevance score, then by date (newer first)
        sorted_news = sorted(
            news_items,
            key=lambda n: (
                -n.relevance_score,
                n.published_at if n.published_at else datetime.min,
            ),
        )
        
        return sorted_news[:limit]
    
    def get_source_scores(
        self,
        sources: List[str],
    ) -> List[SourceScore]:
        """
        Get source reliability scores.
        
        Args:
            sources: List of source names
            
        Returns:
            List of SourceScore objects
        """
        source_scores = []
        for source in sources:
            score = SOURCE_SCORES.get(source, 0.5)
            is_mock = score <= 0.5
            source_scores.append(SourceScore(
                source=source,
                score=score,
                is_mock=is_mock,
            ))
        
        # Sort by score descending
        source_scores.sort(key=lambda s: -s.score)
        return source_scores


# Singleton instance
_ranking_service: Optional[RankingService] = None


def get_ranking_service() -> RankingService:
    """Get the ranking service singleton."""
    global _ranking_service
    if _ranking_service is None:
        _ranking_service = RankingService()
    return _ranking_service


def rank_products(
    candidates: List[ProductCandidate],
    task: ProductTask,
    include_rejected: bool = False,
) -> Tuple[Optional[ProductCandidate], List[ProductCandidate]]:
    """Rank products and select the best one."""
    service = get_ranking_service()
    return service.rank_products(candidates, task, include_rejected)


def rank_products_extended(
    candidates: List[ProductCandidate],
    task: ProductTask,
) -> Tuple[Optional[ProductCandidate], List[ProductCandidate], List[ProductCandidate]]:
    """Rank products and return rejected products."""
    service = get_ranking_service()
    return service.rank_products_extended(candidates, task)


def rank_news(
    news_items: List[NewsItem],
    limit: int = 5,
) -> List[NewsItem]:
    """Rank news items."""
    service = get_ranking_service()
    return service.rank_news(news_items, limit)


def get_source_scores(sources: List[str]) -> List[SourceScore]:
    """Get source scores."""
    service = get_ranking_service()
    return service.get_source_scores(sources)
