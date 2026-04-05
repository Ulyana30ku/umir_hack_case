"""MCP Server - Central server coordinating registry, executor, and safety."""

from typing import Dict, Any, Optional, List
from app.mcp.models import (
    MCPTool,
    ExecutionContext,
    ToolResult,
    ToolManifest,
    SafetyConfig,
    ExecutionPlan,
    ExecutionStep,
)
from app.mcp.registry import MCPToolRegistry, get_registry, init_registry
from app.mcp.executor import MCPExecutor, RetryableExecutor
from app.mcp.safety import SafetyLayer
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPServer:
    """
    MCP Server - central coordinator for tool execution.
    
    Provides:
    - Tool registry and discovery
    - Safe tool execution with validation
    - Execution planning
    - Retry logic
    """
    
    def __init__(self, safety_config: Optional[SafetyConfig] = None):
        """
        Initialize MCP server.
        
        Args:
            safety_config: Safety configuration (uses default if not provided)
        """
        self.registry = MCPToolRegistry()
        self.safety_config = safety_config or SafetyConfig()
        self.safety = SafetyLayer(self.safety_config)
        self.executor = MCPExecutor(self.registry, self.safety)
        self.retry_executor = RetryableExecutor(
            self.registry,
            self.safety,
            max_retries=self.safety_config.max_retries,
        )
        self._initialized = False
    
    def register_tool(self, tool: MCPTool) -> None:
        """Register a tool with the server."""
        self.registry.register(tool)
    
    def register_tools(self, tools: List[MCPTool]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        return self.registry.get(name)
    
    def list_tools(self) -> List[ToolManifest]:
        """List all available tools."""
        return self.registry.list_tools()
    
    def list_tools_by_category(self) -> Dict[str, List[ToolManifest]]:
        """List tools grouped by category."""
        return self.registry.list_by_category()
    
    async def execute_tool(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
        reasoning: Optional[str] = None,
    ) -> ToolResult:
        """
        Execute a single tool.
        
        This is the main entry point for tool execution.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for tool
            context: Execution context
            reasoning: Why this tool was chosen (for tracing)
            
        Returns:
            ToolResult with output or error
        """
        return await self.executor.execute(
            tool_name=tool_name,
            input_data=input_data,
            context=context,
            reasoning=reasoning,
        )
    
    async def execute_tool_with_retry(
        self,
        tool_name: str,
        input_data: Dict[str, Any],
        context: ExecutionContext,
    ) -> ToolResult:
        """Execute tool with retry on failure."""
        return await self.retry_executor.execute_with_retry(
            tool_name=tool_name,
            input_data=input_data,
            context=context,
        )
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        context: ExecutionContext,
    ) -> List[ToolResult]:
        """
        Execute a full execution plan.
        
        Args:
            plan: Execution plan with steps
            context: Execution context
            
        Returns:
            List of ToolResults in order
        """
        results = []
        
        for step in plan.steps:
            logger.info(f"Executing step {step.step_id}: {step.tool_name}")
            
            # Execute step
            result = await self.executor.execute(
                tool_name=step.tool_name,
                input_data=step.input_data,
                context=context,
                step_id=step.step_id,
                reasoning=step.reasoning,
            )
            
            # Update step status
            step.output = result.output
            step.error = result.error
            
            if result.success:
                step.status = "completed"
            else:
                step.status = "failed"
                # Stop on first failure
                logger.warning(f"Step {step.step_id} failed: {result.error}")
                break
            
            results.append(result)
        
        return results
    
    async def execute_steps_parallel(
        self,
        steps: List[ExecutionStep],
        context: ExecutionContext,
    ) -> List[ToolResult]:
        """Execute steps that have no dependencies in parallel."""
        import asyncio
        
        results = []
        
        # Group by dependency level
        ready_steps = [s for s in steps if not s.depends_on]
        remaining = [s for s in steps if s.depends_on]
        
        while ready_steps:
            # Execute ready steps in parallel
            tasks = [
                self.executor.execute(
                    tool_name=step.tool_name,
                    input_data=step.input_data,
                    context=context,
                    step_id=step.step_id,
                    reasoning=step.reasoning,
                )
                for step in ready_steps
            ]
            
            step_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for step, result in zip(ready_steps, step_results):
                if isinstance(result, Exception):
                    step.status = "failed"
                    step.error = str(result)
                    results.append(ToolResult(success=False, error=str(result)))
                else:
                    step.output = result.output
                    step.error = result.error
                    step.status = "completed" if result.success else "failed"
                    results.append(result)
            
            # Find next ready steps
            completed_ids = {s.step_id for s in ready_steps if s.status == "completed"}
            ready_steps = [
                s for s in remaining
                if all(dep_id in completed_ids for dep_id in s.depends_on)
            ]
            remaining = [s for s in remaining if s not in ready_steps]
        
        return results
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities."""
        tools_by_category = self.list_tools_by_category()
        
        return {
            "total_tools": len(self.registry.get_all()),
            "categories": list(tools_by_category.keys()),
            "tools_by_category": {
                cat: len(tools) 
                for cat, tools in tools_by_category.items()
            },
            "safety": {
                "domain_allowlist": self.safety_config.domain_allowlist,
                "action_denylist": self.safety_config.action_denylist,
                "max_steps": self.safety_config.max_steps_per_run,
                "headless_mode": self.safety_config.headless_mode,
            },
            "features": {
                "retry": True,
                "parallel_execution": True,
                "safety_checks": True,
            }
        }


# Global server instance
_mcp_server: Optional[MCPServer] = None


def get_mcp_server() -> MCPServer:
    """Get global MCP server instance, initializing tools if needed."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPServer()
    
    # Lazy initialization of tools if registry is empty
    if len(_mcp_server.list_tools()) == 0:
        try:
            from app.tools import get_all_tools
            tools = get_all_tools()
            _mcp_server.register_tools(tools)
            logger.info(f"Lazy initialized MCP server with {len(tools)} tools")
        except Exception as e:
            logger.warning(f"Failed lazy tool init: {e}")
    return _mcp_server


def init_mcp_server(
    tools: Optional[List[MCPTool]] = None,
    safety_config: Optional[SafetyConfig] = None,
) -> MCPServer:
    """
    Initialize MCP server with tools.
    
    Args:
        tools: List of tools to register
        safety_config: Safety configuration
        
    Returns:
        Initialized MCP server
    """
    global _mcp_server
    
    _mcp_server = MCPServer(safety_config=safety_config)
    
    if tools:
        _mcp_server.register_tools(tools)
    
    logger.info(f"Initialized MCP server with {len(tools or [])} tools")
    
    return _mcp_server


def reset_mcp_server() -> None:
    """Reset the global MCP server."""
    global _mcp_server
    _mcp_server = None
    logger.info("MCP Server reset")
