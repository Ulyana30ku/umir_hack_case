"""Base marketplace connector interface."""

from abc import ABC, abstractmethod
from typing import List

from app.schemas.product import ProductCandidate, ProductSearchResult
from app.schemas.query import ProductTask


class BaseMarketplace(ABC):
    """Abstract base class for marketplace connectors."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Marketplace name."""
        pass
    
    @abstractmethod
    async def search_products(
        self,
        task: ProductTask,
        limit: int = 20,
    ) -> ProductSearchResult:
        """
        Search for products matching the task.
        
        Args:
            task: Product search task
            limit: Maximum number of results
            
        Returns:
            ProductSearchResult with matching products
        """
        pass
    
    @abstractmethod
    async def extract_product_fields(
        self,
        product: ProductCandidate,
    ) -> ProductCandidate:
        """
        Extract additional fields from product page.
        
        Args:
            product: Product candidate to extract from
            
        Returns:
            Product candidate with extracted fields
        """
        pass
