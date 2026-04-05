"""Final response schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.product import ProductCandidate
from app.schemas.news import NewsItem
from app.schemas.trace import AgentRunTrace


class SourceScore(BaseModel):
    """Source ranking score."""
    source: str = Field(..., description="Source name")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Source reliability score")
    is_mock: bool = Field(False, description="Whether this is mock/demo data")


class FinalAnswer(BaseModel):
    """Final response to user query."""
    summary: str = Field(..., description="Short summary of the answer")
    selected_product: Optional[ProductCandidate] = Field(None, description="Best matching product")
    alternative_products: List[ProductCandidate] = Field(default_factory=list, description="Alternative products")
    rejected_products: List[ProductCandidate] = Field(default_factory=list, description="Rejected product candidates with reasons")
    news: List[NewsItem] = Field(default_factory=list, description="Relevant news items")
    sources: List[str] = Field(default_factory=list, description="Sources used")
    source_scores: List[SourceScore] = Field(default_factory=list, description="Source ranking scores")
    explanation: str = Field(..., description="Explanation of the choice")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Overall confidence score")
    trace: AgentRunTrace = Field(..., description="Full execution trace")
    # New fields for external sources tracking
    data_origin: str = Field("external", description="Origin of data: external, cached, mixed")
    retrieval_mode: str = Field("live", description="Retrieval mode: live, live_cached, cached")
    unavailable_sources: List[str] = Field(default_factory=list, description="Sources that failed or were unavailable")


class ExecutionPlan(BaseModel):
    """Execution plan for agent tasks."""
    run_product_search: bool = Field(False, description="Whether to run product search")
    run_news_search: bool = Field(False, description="Whether to run news search")
    steps: List[str] = Field(default_factory=list, description="Ordered list of steps to execute")
