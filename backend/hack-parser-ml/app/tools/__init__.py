"""Tool initialization - registers all tools with MCP server."""

from typing import List, Optional
from app.mcp.models import MCPTool, SafetyConfig
from app.mcp.server import MCPServer, init_mcp_server
from app.tools.browser.actions import BROWSER_TOOLS
from app.tools.browser.extractors import EXTRACTION_TOOLS
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_all_tools() -> List[MCPTool]:
    """
    Get all available tools.
    
    Returns:
        List of all MCPTool instances
    """
    tools = []
    
    # Add browser tools
    tools.extend(BROWSER_TOOLS)
    
    # Add extraction tools
    tools.extend(EXTRACTION_TOOLS)
    
    # Add workflow tools (will be added in later stages)
    # tools.extend(WORKFLOW_TOOLS)
    
    return tools


def init_tools(
    safety_config: Optional[SafetyConfig] = None,
) -> MCPServer:
    """
    Initialize MCP server with all tools.
    
    Args:
        safety_config: Optional safety configuration
        
    Returns:
        Initialized MCP server
    """
    tools = get_all_tools()
    
    logger.info(f"Initializing tools: {len(tools)} tools")
    
    server = init_mcp_server(
        tools=tools,
        safety_config=safety_config,
    )
    
    logger.info(f"Tools initialized successfully")
    
    return server


# Export server initialization
__all__ = [
    "get_all_tools",
    "init_tools",
]
