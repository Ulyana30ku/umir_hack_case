"""Query parsing schemas."""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Type of user intent."""
    BROWSER_NAVIGATION = "browser_navigation"
    BROWSER_INTERACTION = "browser_interaction"
    INFO_RETRIEVAL = "info_retrieval"
    PRODUCT_SEARCH = "product_search"
    NEWS_SEARCH = "news_search"
    MULTI_STEP = "multi_step"
    UNKNOWN = "unknown"


class ExecutionHints(BaseModel):
    """Execution hints for the planner."""
    requires_browser: bool = Field(True, description="Whether the task requires browser automation")
    requires_extraction: bool = Field(False, description="Whether the task requires data extraction")
    requires_multi_step_plan: bool = Field(False, description="Whether the task requires multi-step planning")
    target_url: Optional[str] = Field(None, description="Target URL if specified in query")
    button_text: Optional[str] = Field(None, description="Button text to click if specified")
    input_text: Optional[str] = Field(None, description="Text to input if specified")
    search_query: Optional[str] = Field(None, description="Search query if specified")
    page_action: Optional[str] = Field(None, description="Page action: scroll, back, refresh")


class ProductTask(BaseModel):
    """Extracted product search task from user query."""
    category: Optional[str] = Field(None, description="Product category (e.g., 'смартфон', 'ноутбук')")
    brand: Optional[str] = Field(None, description="Brand name (e.g., 'Apple', 'Samsung')")
    model_family: Optional[str] = Field(None, description="Model family (e.g., 'iPhone', 'Galaxy')")
    model: Optional[str] = Field(None, description="Specific model name")
    memory_gb: Optional[int] = Field(None, description="Storage size in GB")
    ram_gb: Optional[int] = Field(None, description="RAM size in GB")
    color: Optional[str] = Field(None, description="Product color")
    condition: Optional[str] = Field(None, description="Condition: 'new', 'used', 'refurbished'")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    sort_by: Optional[str] = Field(None, description="Sort order: 'price_asc', 'price_desc', 'rating'")


class NewsTask(BaseModel):
    """Extracted news search task from user query."""
    topic: Optional[str] = Field(None, description="News topic/keyword")
    period_days: Optional[int] = Field(7, description="Number of days to look back")
    limit: int = Field(5, description="Maximum number of news items")
    language: Optional[str] = Field(None, description="Language code (e.g., 'ru', 'en')")


class ParsedUserQuery(BaseModel):
    """Parsed user query with extracted tasks and metadata."""
    raw_query: str = Field(..., description="Original user query")
    normalized_query: Optional[str] = Field(None, description="Normalized version of the query")
    intent_type: IntentType = Field(IntentType.UNKNOWN, description="Detected intent type")
    execution_hints: Optional[ExecutionHints] = Field(None, description="Execution hints for planner")
    product_task: Optional[ProductTask] = Field(None, description="Extracted product search task")
    news_task: Optional[NewsTask] = Field(None, description="Extracted news search task")
    ambiguities: List[str] = Field(default_factory=list, description="Ambiguities found in query")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made during parsing")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score of parsing")
