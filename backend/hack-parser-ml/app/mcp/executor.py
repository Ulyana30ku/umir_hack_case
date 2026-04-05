"""MCP Executor - Tool execution engine with validation and tracing."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.mcp.models import (
    MCPTool, 
    ExecutionContext, 
    ToolResult, 
    ExecutionStep,
    SafetyConfig,
    SafetyViolationError,
    ToolNotFoundError,
)
from app.mcp.registry import MCPToolRegistry
from app.mcp.safety import SafetyLayer, SafetyResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPExecutor:
    """
    MCP Executor - executes tools with safety checks, validation, and tracing.
    
    This is the ONLY way to execute tools - never call tool.execute() directly.
    """
    
    def __init__(
        self, 
        registry: MCPToolRegistry,
        safety_layer: SafetyLayer,
    ):
        """
        Initialize executor.
        
        Args:
            registry: Tool registry
            safety_layer: Safety layer for checking actions
        """
        self.registry = registry
        self.safety = safety_layer
    
    async def execute(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
        step_id: Optional[str] = None,
        reasoning: Optional[str] = None,
    ) -> ToolResult:
        """
        Execute a tool with full MCP pipeline.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for tool
            context: Execution context
            step_id: Step ID for tracing
            reasoning: Why this tool was chosen
            
        Returns:
            ToolResult with output or error
            
        Raises:
            ToolNotFoundError: If tool not found
            SafetyViolationError: If action blocked by safety
        """
        start_time = time.time()
        
        # 1. TOOL DISCOVERY - Get tool from registry
        tool = self.registry.get(tool_name)
        if tool is None:
            error_msg = f"Tool not found: {tool_name}"
            logger.error(error_msg)
            raise ToolNotFoundError(error_msg)
        
        logger.info(f"Executing tool: {tool_name} (step: {step_id})")
        if reasoning:
            logger.debug(f"Reasoning: {reasoning}")
        
        try:
            # 2. SAFETY CHECK - Before ANY execution
            safety_result = await self.safety.check(
                tool_name=tool_name,
                input_data=input_data,
                context=context,
            )
            if not safety_result.allowed:
                raise SafetyViolationError(safety_result.reason)
            
            # 3. INPUT VALIDATION
            try:
                validated_input = tool.validate_input(input_data)
            except ValueError as e:
                return ToolResult(
                    success=False,
                    error=f"Input validation failed: {str(e)}",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )
            
            # 4. CONTEXT UPDATE
            context.increment_step()
            
            # 5. EXECUTE TOOL
            result = await tool.execute(validated_input, context)
            
            # 6. OUTPUT VALIDATION
            try:
                validated_output = tool.validate_output(result.output)
                result.output = validated_output
            except ValueError as e:
                logger.warning(f"Output validation warning: {e}")
            
            # 7. UPDATE BROWSER STATE if applicable
            if hasattr(tool, 'category') and tool.category == 'browser':
                await self._update_browser_state(tool_name, input_data, result, context)
            
            # Calculate execution time
            result.execution_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Tool {tool_name} completed in {result.execution_time_ms}ms, "
                f"success: {result.success}"
            )
            
            return result
            
        except SafetyViolationError as e:
            logger.warning(f"Safety violation for {tool_name}: {e.reason}")
            return ToolResult(
                success=False,
                error=f"Safety violation: {e.reason}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
            
        except Exception as e:
            logger.error(f"Tool execution error for {tool_name}: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                execution_time_ms=int((time.time() - start_time) * 1000),
            )
    
    async def execute_plan(
        self,
        plan_steps: List[ExecutionStep],
        context: ExecutionContext,
    ) -> List[ToolResult]:
        """
        Execute a full plan with steps.
        
        Args:
            plan_steps: List of execution steps
            context: Execution context
            
        Returns:
            List of ToolResults in order
        """
        results: List[ToolResult] = []
        
        for step in plan_steps:
            logger.info(f"Executing step {step.step_id}: {step.tool_name}")
            
            # Execute the step
            result = await self.execute(
                tool_name=step.tool_name,
                input_data=step.input_data,
                context=context,
                step_id=step.step_id,
                reasoning=step.reasoning,
            )
            
            # Update step status
            step.output = result.output
            step.error = result.error
            step.status = "completed" if result.success else "failed"
            step.started_at = datetime.now()
            step.finished_at = datetime.now()
            
            results.append(result)
            
            # If step failed and it's critical, stop
            if not result.success and self._is_critical_step(step.tool_name):
                logger.warning(f"Critical step {step.step_id} failed, stopping execution")
                break
        
        return results
    
    async def _update_browser_state(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        result: ToolResult,
        context: ExecutionContext,
    ) -> None:
        """Update browser state after tool execution."""
        state = context.browser_state
        
        if tool_name == "browser.open_url" and result.success:
            state.history.append(state.current_url)
            state.current_url = result.output.get("url", "")
            state.page_title = result.output.get("title", "")
            
        elif tool_name == "browser.go_back" and result.success:
            if state.history:
                state.current_url = state.history[-1]
                state.history = state.history[:-1]
                
        elif tool_name == "browser.get_page_text":
            state.last_html_snapshot = result.output.get("text", "")[:10000]
            
        elif tool_name == "browser.screenshot":
            state.last_screenshot = result.output.get("path")
    
    def _is_critical_step(self, tool_name: str) -> bool:
        """Check if step failure should stop execution."""
        critical_tools = ["browser.open_url", "browser.click"]
        return tool_name in critical_tools


class RetryableExecutor(MCPExecutor):
    """Executor with retry logic."""
    
    def __init__(
        self,
        registry: MCPToolRegistry,
        safety_layer: SafetyLayer,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        super().__init__(registry, safety_layer)
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    async def execute_with_retry(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        """Execute tool with retry on failure."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self.execute(tool_name, input_data, context)
                
                if result.success:
                    return result
                    
                last_error = result.error
                
            except Exception as e:
                last_error = str(e)
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                delay = self.base_delay * (2 ** attempt)
                logger.info(f"Retry {attempt + 1}/{self.max_retries} for {tool_name} after {delay}s")
                import asyncio
                await asyncio.sleep(delay)
        
        return ToolResult(
            success=False,
            error=f"Failed after {self.max_retries} attempts: {last_error}",
        )
