"""Tests for validation service."""

import pytest

from app.services.validation_service import ValidationService
from app.schemas.product import ProductCandidate
from app.schemas.query import ProductTask


class TestValidationService:
    """Test cases for ValidationService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ValidationService()
    
    def test_validate_brand_match(self):
        """Test brand validation when matching."""
        task = ProductTask(brand="Apple")
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="iPhone 15",
            brand="Apple",
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert "brand" in result.matched_constraints
        assert result.rejection_reason is None
    
    def test_validate_brand_mismatch(self):
        """Test brand validation when not matching."""
        task = ProductTask(brand="Apple")
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="Samsung Galaxy",
            brand="Samsung",
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert "brand" in result.unmet_constraints
        assert result.rejection_reason is not None
    
    def test_validate_memory_match(self):
        """Test memory validation when matching."""
        task = ProductTask(memory_gb=256)
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="iPhone 256GB",
            memory_gb=256,
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert "memory_gb" in result.matched_constraints
    
    def test_validate_memory_mismatch(self):
        """Test memory validation when not matching."""
        task = ProductTask(memory_gb=256)
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="iPhone 128GB",
            memory_gb=128,
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert "memory_gb" in result.unmet_constraints
    
    def test_validate_condition_match(self):
        """Test condition validation when matching."""
        task = ProductTask(condition="new")
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="New iPhone",
            condition="new",
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert "condition" in result.matched_constraints
    
    def test_validate_condition_mismatch(self):
        """Test condition validation when not matching."""
        task = ProductTask(condition="new")
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="Used iPhone",
            condition="used",
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert "condition" in result.unmet_constraints
    
    def test_validate_price_range(self):
        """Test price range validation."""
        task = ProductTask(min_price=50000, max_price=150000)
        
        # Test price in range
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="iPhone",
            price=100000,
            url="https://example.com",
        )
        result = self.service.validate_product(candidate, task)
        assert "max_price" in result.matched_constraints
        assert "min_price" in result.matched_constraints
        
        # Test price above max
        candidate.price = 200000
        result = self.service.validate_product(candidate, task)
        assert "max_price" in result.unmet_constraints
        
        # Test price below min
        candidate.price = 10000
        result = self.service.validate_product(candidate, task)
        assert "min_price" in result.unmet_constraints
    
    def test_validate_multiple_constraints(self):
        """Test validating multiple constraints."""
        task = ProductTask(
            brand="Apple",
            memory_gb=256,
            condition="new",
        )
        candidate = ProductCandidate(
            id="test-1",
            source="Test",
            title="New iPhone 256GB",
            brand="Apple",
            memory_gb=256,
            condition="new",
            url="https://example.com",
        )
        
        result = self.service.validate_product(candidate, task)
        
        assert len(result.matched_constraints) == 3
        assert result.rejection_reason is None
    
    def test_filter_valid(self):
        """Test filtering valid candidates."""
        task = ProductTask(brand="Apple")
        
        candidates = [
            ProductCandidate(id="1", source="Test", title="Apple", brand="Apple", url="https://1"),
            ProductCandidate(id="2", source="Test", title="Samsung", brand="Samsung", url="https://2"),
            ProductCandidate(id="3", source="Test", title="Apple 2", brand="Apple", url="https://3"),
        ]
        
        validated = self.service.validate_products(candidates, task)
        valid = self.service.filter_valid(validated)
        
        assert len(valid) == 2
    
    def test_filter_by_constraints(self):
        """Test filtering by required constraints."""
        task = ProductTask(brand="Apple", condition="new")
        
        candidates = [
            ProductCandidate(
                id="1", source="Test", title="Apple new", brand="Apple",
                condition="new", matched_constraints=["brand", "condition"], url="https://1"
            ),
            ProductCandidate(
                id="2", source="Test", title="Apple used", brand="Apple",
                condition="used", matched_constraints=["brand"], url="https://2"
            ),
        ]
        
        filtered = self.service.filter_by_constraints(candidates, ["brand", "condition"])
        
        assert len(filtered) == 1
        assert filtered[0].id == "1"


def test_validation_service_singleton():
    """Test that validation service singleton works."""
    from app.services.validation_service import get_validation_service
    
    service1 = get_validation_service()
    service2 = get_validation_service()
    
    assert service1 is service2
