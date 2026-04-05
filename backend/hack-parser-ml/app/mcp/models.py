"""MCP Models - Core definitions for MCP tool execution."""

from typing import Any, Dict, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    """Tool category types."""
    BROWSER = "browser"
    EXTRACTION = "extraction"
    WORKFLOW = "workflow"
    DOMAIN = "domain"
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    WAIT = "wait"


class ToolStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ============ Tool Schemas ============

class ToolManifest(BaseModel):
    """Tool manifest for discovery."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for input")
    output_schema: Dict[str, Any] = Field(..., description="JSON Schema for output")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    category: str = Field(..., description="Tool category")


# ============ Execution Context ============

class BrowserState(BaseModel):
    """Browser session state."""
    current_url: str = ""
    page_title: str = ""
    history: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    viewport: Dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})
    errors: List[str] = field(default_factory=list)
    last_screenshot: Optional[str] = None
    last_html_snapshot: Optional[str] = None


class ExecutionContext(BaseModel):
    """Context for tool execution."""
    run_id: str
    session_id: str
    browser_state: BrowserState = Field(default_factory=BrowserState)
    step_count: int = 0
    max_steps: int = 50
    start_time: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def increment_step(self) -> None:
        """Increment step counter."""
        self.step_count += 1


# ============ Tool Result ============

class ToolResult(BaseModel):
    """Result of tool execution."""
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: int = 0
    screenshot_path: Optional[str] = None
    html_snapshot: Optional[str] = None


# ============ MCP Tool Base ============

class MCPTool:
    """Base class for MCP tools - must be used through MCP executor."""
    
    name: str = ""
    description: str = ""
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}
    tags: List[str] = []
    category: str = ""
    
    def __init__(self):
        """Initialize tool."""
        if not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must have a name")
    
    def get_manifest(self) -> ToolManifest:
        """Get tool manifest for discovery."""
        return ToolManifest(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
            output_schema=self.output_schema,
            tags=self.tags,
            category=self.category,
        )
    
    async def execute(
        self, 
        input_data: Dict[str, Any], 
        context: ExecutionContext
    ) -> ToolResult:
        """
        Execute the tool.
        
        NOTE: This should NOT be called directly.
        Always use MCPExecutor.execute() to ensure:
        - Safety checks are performed
        - Input validation is done
        - Trace is recorded
        - Output validation is done
        """
        raise NotImplementedError(f"Tool {self.name} must implement execute()")
    
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against schema."""
        # Basic validation - can be extended with jsonschema
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in input_data:
                raise ValueError(f"Missing required field: {field}")
        return input_data
    
    def validate_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output data against schema."""
        # Basic validation - can be extended with jsonschema
        return output


# ============ Execution Step ============

class ExecutionStep(BaseModel):
    """Single step in execution plan."""
    step_id: str = Field(..., description="Unique step identifier")
    tool_name: str = Field(..., description="Tool to execute")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Input data for tool")
    reasoning: str = Field(..., description="Why this tool was chosen")
    depends_on: List[str] = Field(default_factory=list, description="Step IDs this depends on")
    status: ToolStatus = Field(default=ToolStatus.PENDING)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    
    def duration_ms(self) -> int:
        """Calculate duration in milliseconds."""
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return 0


class ExecutionPlan(BaseModel):
    """Execution plan with steps."""
    plan_id: str = Field(..., description="Unique plan identifier")
    query: str = Field(..., description="Original user query")
    steps: List[ExecutionStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    
    def get_step(self, step_id: str) -> Optional[ExecutionStep]:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_ready_steps(self) -> List[ExecutionStep]:
        """Get steps that are ready to execute (dependencies met)."""
        ready = []
        for step in self.steps:
            if step.status != ToolStatus.PENDING:
                continue
            # Check if all dependencies are completed
            deps_met = True
            for dep_id in step.depends_on:
                dep_step = self.get_step(dep_id)
                if dep_step is None or dep_step.status != ToolStatus.COMPLETED:
                    deps_met = False
                    break
            if deps_met:
                ready.append(step)
        return ready


# ============ Safety Models ============

class SafetyConfig(BaseModel):
    """Safety configuration for browser automation."""
    domain_allowlist: List[str] = Field(
        default_factory=list,
        description="Allowed domains (empty = allow all)"
    )
    action_denylist: List[str] = Field(
        default_factory=lambda: ["eval", "exec", "innerHTML", "download_file"],
        description="Blocked actions"
    )
    max_steps_per_run: int = Field(default=50, description="Maximum steps per run")
    headless_mode: bool = Field(default=True, description="Run browser in headless mode")
    screenshot_on_error: bool = Field(default=True, description="Take screenshot on error")
    max_retries: int = Field(default=3, description="Max retries per step")


class SafetyViolationError(Exception):
    """Raised when action is blocked by safety layer."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Safety violation: {reason}")


class ToolNotFoundError(Exception):
    """Raised when tool is not found in registry."""
    pass
