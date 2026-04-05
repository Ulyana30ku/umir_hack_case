"""Task execution schemas."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class StepStatus(str, Enum):
    """Status of an execution step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStep(BaseModel):
    """A single step in the execution plan."""
    step_id: str = Field(..., description="Unique step ID")
    step_order: int = Field(..., description="Order of step in plan")
    tool_name: str = Field(..., description="Tool to call")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input for tool")
    status: StepStatus = Field(StepStatus.PENDING, description="Step status")
    output_data: Optional[Dict[str, Any]] = Field(None, description="Output from tool")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: Optional[str] = Field(None, description="ISO timestamp when started")
    finished_at: Optional[str] = Field(None, description="ISO timestamp when finished")


class ExecutionPlan(BaseModel):
    """Execution plan created by the planner."""
    plan_id: str = Field(..., description="Unique plan ID")
    intent_type: str = Field(..., description="Intent type from query")
    steps: List[ExecutionStep] = Field(default_factory=list, description="Steps to execute")
    requires_browser: bool = Field(True, description="Whether plan needs browser")
    estimated_steps: int = Field(0, description="Estimated number of steps")
    
    def add_step(self, step: ExecutionStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
    
    def get_next_step(self) -> Optional[ExecutionStep]:
        """Get the next pending step."""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                return step
        return None
    
    def mark_step_running(self, step_id: str) -> None:
        """Mark a step as running."""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.RUNNING
                break
    
    def mark_step_completed(self, step_id: str, output: Dict[str, Any]) -> None:
        """Mark a step as completed."""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.COMPLETED
                step.output_data = output
                break
    
    def mark_step_failed(self, step_id: str, error: str) -> None:
        """Mark a step as failed."""
        for step in self.steps:
            if step.step_id == step_id:
                step.status = StepStatus.FAILED
                step.error = error
                break
    
    def is_complete(self) -> bool:
        """Check if all steps are complete."""
        return all(s.status in (StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED) 
                   for s in self.steps)
    
    def has_failures(self) -> bool:
        """Check if any step failed."""
        return any(s.status == StepStatus.FAILED for s in self.steps)