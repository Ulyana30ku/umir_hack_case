"""Tests for ranking service."""

import pytest

from app.services.ranking_service import RankingService
from app.schemas.product import ProductCandidate
from app.schemas.news import NewsItem
from app.schemas.query import ProductTask


class TestRankingService:
    """Test cases for RankingService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = RankingService()
    
    def test_rank_products_by_price(self):
        """Test ranking products by price."""
        task = ProductTask(sort_by="price_asc")
        
        candidates = [
            ProductCandidate(
                id="1", source="Test", title="Expensive", price=150000, url="https://1"
            ),
            ProductCandidate(
                id="2", source="Test", title="Cheap", price=50000, url="https://2"
            ),
            ProductCandidate(
                id="3", source="Test", title="Medium", price=100000, url="https://3"
            ),
        ]
        
        selected, alternatives = self.service.rank_products(candidates, task)
        
        assert selected.price == 50000
        assert len(alternatives) == 2
    
    def test_rank_products_by_matched_constraints(self):
        """Test ranking products by matched constraints."""
        task = ProductTask()
        
        candidates = [
            ProductCandidate(
                id="1",
                source="Test",
                title="One match",
                matched_constraints=["brand"],
                url="https://1",
            ),
            ProductCandidate(
                id="2",
                source="Test",
                title="Two matches",
                matched_constraints=["brand", "memory_gb"],
                url="https://2",
            ),
        ]
        
        selected, alternatives = self.service.rank_products(candidates, task)
        
        assert selected.id == "2"
    
    def test_rank_products_empty_list(self):
        """Test ranking with empty list."""
        task = ProductTask()
        
        selected, alternatives = self.service.rank_products([], task)
        
        assert selected is None
        assert alternatives == []
    
    def test_rank_products_filters_rejected(self):
        """Test that ranking filters out rejected products."""
        task = ProductTask()
        
        candidates = [
            ProductCandidate(
                id="1",
                source="Test",
                title="Valid",
                rejection_reason=None,
                price=100000,
                url="https://1",
            ),
            ProductCandidate(
                id="2",
                source="Test",
                title="Rejected",
                rejection_reason="Brand mismatch",
                price=50000,
                url="https://2",
            ),
        ]
        
        selected, alternatives = self.service.rank_products(candidates, task)
        
        assert selected.id == "1"
    
    def test_rank_news_by_relevance(self):
        """Test ranking news by relevance."""
        news_items = [
            NewsItem(id="1", title="Low relevance", source="Test", url="https://1", relevance_score=0.3),
            NewsItem(id="2", title="High relevance", source="Test", url="https://2", relevance_score=0.9),
            NewsItem(id="3", title="Medium relevance", source="Test", url="https://3", relevance_score=0.6),
        ]
        
        ranked = self.service.rank_news(news_items, limit=2)
        
        assert ranked[0].id == "2"
        assert ranked[1].id == "3"
        assert len(ranked) == 2
    
    def test_rank_news_empty_list(self):
        """Test ranking with empty news list."""
        ranked = self.service.rank_news([])
        
        assert ranked == []


def test_ranking_service_singleton():
    """Test that ranking service singleton works."""
    from app.services.ranking_service import get_ranking_service
    
    service1 = get_ranking_service()
    service2 = get_ranking_service()
    
    assert service1 is service2
