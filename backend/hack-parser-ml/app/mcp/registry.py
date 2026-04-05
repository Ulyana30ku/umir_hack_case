"""MCP Registry - Tool catalog and discovery."""

from typing import Dict, List, Optional, Any
from app.mcp.models import MCPTool, ToolManifest, ToolCategory
from app.core.logging import get_logger

logger = get_logger(__name__)


class MCPToolRegistry:
    """MCP-compatible tool registry - manages all available tools."""
    
    def __init__(self):
        """Initialize empty registry."""
        self._tools: Dict[str, MCPTool] = {}
        self._initialized = False
    
    def register(self, tool: MCPTool) -> None:
        """
        Register a tool.
        
        Args:
            tool: MCPTool instance to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} (category: {tool.category})")
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[MCPTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            MCPTool instance or None if not found
        """
        return self._tools.get(name)
    
    def get_all(self) -> List[MCPTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_by_category(self, category: str) -> List[MCPTool]:
        """
        Get tools by category.
        
        Args:
            category: Tool category to filter by
            
        Returns:
            List of tools in category
        """
        return [
            tool for tool in self._tools.values()
            if tool.category == category
        ]
    
    def get_by_tag(self, tag: str) -> List[MCPTool]:
        """
        Get tools by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of tools with tag
        """
        return [
            tool for tool in self._tools.values()
            if tag in tool.tags
        ]
    
    def list_tools(self) -> List[ToolManifest]:
        """
        List all tools with their manifests.
        
        Returns:
            List of ToolManifest for discovery
        """
        return [tool.get_manifest() for tool in self._tools.values()]
    
    def list_by_category(self) -> Dict[str, List[ToolManifest]]:
        """
        List tools grouped by category.
        
        Returns:
            Dict mapping category to list of tools
        """
        result: Dict[str, List[ToolManifest]] = {}
        for tool in self._tools.values():
            if tool.category not in result:
                result[tool.category] = []
            result[tool.category].append(tool.get_manifest())
        return result


# Global registry instance
_registry: Optional[MCPToolRegistry] = None


def get_registry() -> MCPToolRegistry:
    """Get global MCP tool registry instance."""
    global _registry
    if _registry is None:
        _registry = MCPToolRegistry()
    return _registry


def init_registry(tools: Optional[List[MCPTool]] = None) -> MCPToolRegistry:
    """
    Initialize tool registry with tools.
    
    Args:
        tools: List of tools to register (optional)
        
    Returns:
        Initialized registry
    """
    registry = get_registry()
    
    if registry._initialized:
        logger.warning("Registry already initialized")
        return registry
    
    # If tools provided, register them
    if tools:
        for tool in tools:
            registry.register(tool)
    
    registry._initialized = True
    logger.info(f"Initialized MCP registry with {len(registry.get_all())} tools")
    
    return registry


def reset_registry() -> None:
    """Reset the global registry."""
    global _registry
    _registry = None
    logger.info("MCP Registry reset")


# Tool decorator for easy registration
def register_tool(category: str = "", tags: Optional[List[str]] = None):
    """
    Decorator to register a tool automatically.
    
    Usage:
        @register_tool(category="browser", tags=["navigation"])
        class MyTool(MCPTool):
            ...
    """
    def decorator(cls):
        # Set category and tags on the class
        if category:
            cls.category = category
        if tags:
            cls.tags = tags
        return cls
    return decorator
