"""Product schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field


class ProductCandidate(BaseModel):
    """Product candidate from marketplace search."""
    id: str = Field(..., description="Unique product identifier")
    source: str = Field(..., description="Source marketplace name")
    title: str = Field(..., description="Product title")
    model: Optional[str] = Field(None, description="Model name")
    brand: Optional[str] = Field(None, description="Brand name")
    memory_gb: Optional[int] = Field(None, description="Storage size in GB")
    ram_gb: Optional[int] = Field(None, description="RAM size in GB")
    color: Optional[str] = Field(None, description="Product color")
    condition: Optional[str] = Field(None, description="Condition: new, used, refurbished")
    seller: Optional[str] = Field(None, description="Seller name")
    price: Optional[float] = Field(None, description="Product price")
    currency: Optional[str] = Field("RUB", description="Currency code")
    rating: Optional[float] = Field(None, ge=0.0, le=5.0, description="Product rating")
    reviews_count: Optional[int] = Field(None, ge=0, description="Number of reviews")
    delivery_info: Optional[str] = Field(None, description="Delivery information")
    url: str = Field(..., description="Product URL")
    raw_text: Optional[str] = Field(None, description="Raw text extracted from page")
    extracted_from: Optional[dict] = Field(None, description="Source data")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Extraction confidence")
    matched_constraints: List[str] = Field(default_factory=list, description="Constraints that are satisfied")
    unmet_constraints: List[str] = Field(default_factory=list, description="Constraints that are not satisfied")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if applicable")


class ProductSearchResult(BaseModel):
    """Result of product search operation."""
    products: List[ProductCandidate] = Field(default_factory=list)
    total_found: int = Field(0, description="Total products found")
    search_query: str = Field(..., description="Query used for search")
