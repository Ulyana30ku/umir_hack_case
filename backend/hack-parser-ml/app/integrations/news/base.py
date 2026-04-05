"""Base news source connector interface."""

from abc import ABC, abstractmethod

from app.schemas.news import NewsItem, NewsSearchResult
from app.schemas.query import NewsTask


class BaseNewsSource(ABC):
    """Abstract base class for news source connectors."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """News source name."""
        pass
    
    @abstractmethod
    async def search_news(
        self,
        task: NewsTask,
    ) -> NewsSearchResult:
        """
        Search for news matching the task.
        
        Args:
            task: News search task
            
        Returns:
            NewsSearchResult with matching news
        """
        pass
