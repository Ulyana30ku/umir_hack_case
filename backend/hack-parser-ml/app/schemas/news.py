"""News schemas."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """News article item."""
    id: str = Field(..., description="Unique news identifier")
    title: str = Field(..., description="News title")
    source: str = Field(..., description="News source name")
    published_at: Optional[datetime] = Field(None, description="Publication datetime")
    url: str = Field(..., description="News article URL")
    snippet: Optional[str] = Field(None, description="News snippet/description")
    topic: Optional[str] = Field(None, description="Topic/keyword")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance score")
    duplicate_group: Optional[str] = Field(None, description="Group ID for duplicates")
    summary: Optional[str] = Field(None, description="AI-generated summary")


class NewsSearchResult(BaseModel):
    """Result of news search operation."""
    news: List[NewsItem] = Field(default_factory=list)
    total_found: int = Field(0, description="Total news items found")
    search_topic: str = Field(..., description="Topic used for search")
