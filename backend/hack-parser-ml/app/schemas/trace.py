"""Trace schemas for agent step tracking."""

from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class SourceAttempt(BaseModel):
    """Single attempt at a source."""
    source: str = Field(..., description="Source name")
    attempt_number: int = Field(..., description="Attempt number (1-based)")
    status: str = Field(..., description="Status: success, failed, rate_limited, timeout")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    cached: bool = Field(False, description="Whether result was from cache")


class SourceResult(BaseModel):
    """Result from a source."""
    source: str = Field(..., description="Source name")
    success: bool = Field(..., description="Whether source succeeded")
    items_count: int = Field(0, description="Number of items returned")
    attempts: List[SourceAttempt] = Field(default_factory=list, description="All attempts for this source")
    failover_used: bool = Field(False, description="Whether failover was used")
    final_source: Optional[str] = Field(None, description="Final source after failover")


class AgentTraceStep(BaseModel):
    """Single step in agent execution trace."""
    step_name: str = Field(..., description="Name of the step")
    status: str = Field(..., description="Status: started, completed, failed")
    
    # Reasoning - why this step was chosen
    reasoning: Optional[str] = Field(None, description="Why this tool/step was chosen")
    
    # Tool execution
    tool_name: Optional[str] = Field(None, description="Tool that was executed")
    input_payload: Optional[dict] = Field(None, description="Input data for the step")
    output_payload: Optional[dict] = Field(None, description="Output data from the step")
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.now, description="Step start time")
    finished_at: Optional[datetime] = Field(None, description="Step finish time")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    
    # Error
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Browser artifacts
    screenshot_path: Optional[str] = Field(None, description="Screenshot path if taken")
    html_snapshot: Optional[str] = Field(None, description="HTML/text snapshot")
    browser_url: Optional[str] = Field(None, description="Browser URL at this step")
    
    # Retry tracking
    retry_count: int = Field(0, description="Number of retries performed")
    # New fields for external sources tracking
    source_used: Optional[str] = Field(None, description="Primary source used")
    source_attempts: List[SourceAttempt] = Field(default_factory=list, description="All source attempts")
    cache_hit: bool = Field(False, description="Whether result was from cache")
    retry_count: int = Field(0, description="Number of retries performed")
    failover_used: bool = Field(False, description="Whether failover was used")
    unavailable_sources: List[str] = Field(default_factory=list, description="Sources that failed")

    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration in seconds."""
        if self.finished_at and self.started_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


class AgentRunTrace(BaseModel):
    """Complete trace of an agent run."""
    run_id: str = Field(..., description="Unique run identifier")
    user_query: str = Field(..., description="Original user query")
    steps: List[AgentTraceStep] = Field(default_factory=list, description="All steps executed")
    final_status: str = Field("pending", description="Final status: success, failed, partial")
    # New fields
    partial_success_reason: Optional[str] = Field(None, description="Reason for partial success")
    total_retries: int = Field(0, description="Total retries across all steps")
    cache_hits: int = Field(0, description="Total cache hits")
    sources_tried: List[str] = Field(default_factory=list, description="All sources attempted")

    def add_step(self, step: AgentTraceStep) -> None:
        """Add a step to the trace."""
        self.steps.append(step)

    def get_step(self, step_name: str) -> Optional[AgentTraceStep]:
        """Get a step by name."""
        for step in self.steps:
            if step.step_name == step_name:
                return step
        return None

    def mark_completed(self, step_name: str, output: Any = None) -> None:
        """Mark a step as completed."""
        step = self.get_step(step_name)
        if step:
            step.status = "completed"
            step.finished_at = datetime.now()
            if output:
                # Properly serialize Pydantic models and other objects
                if hasattr(output, 'model_dump'):
                    # Pydantic v2 model
                    step.output_payload = {"result": output.model_dump()}
                elif hasattr(output, 'dict'):
                    # Pydantic v1 model
                    step.output_payload = {"result": output.dict()}
                elif isinstance(output, dict):
                    step.output_payload = {"result": output}
                elif isinstance(output, list):
                    step.output_payload = {"result": output}
                elif isinstance(output, tuple):
                    # Convert tuple to list for JSON serialization
                    step.output_payload = {"result": list(output)}
                elif isinstance(output, (str, int, float, bool)):
                    # Primitive types
                    step.output_payload = {"result": output}
                else:
                    step.output_payload = {"result": str(output)[:500]}

    def mark_failed(self, step_name: str, error: str) -> None:
        """Mark a step as failed."""
        step = self.get_step(step_name)
        if step:
            step.status = "failed"
            step.finished_at = datetime.now()
            step.error_message = error
