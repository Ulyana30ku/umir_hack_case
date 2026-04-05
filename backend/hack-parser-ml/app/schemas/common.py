"""Common DTOs used across the application."""

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentRunRequest(BaseModel):
    """Request schema for agent run endpoint."""
    query: str = Field(..., description="User query in natural language")
    run_id: Optional[str] = Field(None, description="Optional run ID for tracking")


class AgentRunResponse(BaseModel):
    """Response schema for agent run endpoint."""
    run_id: str
    query: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
