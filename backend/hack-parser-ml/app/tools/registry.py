"""Tool registry for managing all available tools."""

from typing import Dict, List, Optional, Any
from app.tools.browser.base import BaseTool
from app.tools.browser.tools import get_all_browser_tools
from app.core.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Registry for managing all available tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._initialized = False
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool.
        
        Args:
            tool: Tool to register
        """
        if tool.name in self._tools:
            logger.warning(f"Tool {tool.name} already registered, overwriting")
        
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> bool:
        """Unregister a tool.
        
        Args:
            name: Tool name to unregister
            
        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool or None if not found
        """
        return self._tools.get(name)
    
    def get_all(self) -> List[BaseTool]:
        """Get all registered tools.
        
        Returns:
            List of all tools
        """
        return list(self._tools.values())
    
    def get_by_category(self, category: str) -> List[BaseTool]:
        """Get tools by category.
        
        Args:
            category: Tool category
            
        Returns:
            List of tools in category
        """
        return [tool for tool in self._tools.values() 
                if tool.name.startswith(f"{category}_")]
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all tools with their schemas.
        
        Returns:
            List of tool info dicts
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema.__name__ if tool.input_schema else None,
                "output_schema": tool.output_schema.__name__ if tool.output_schema else None,
            }
            for tool in self._tools.values()
        ]
    
    async def execute(self, tool_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for tool
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If tool not found
        """
        tool = self.get(tool_name)
        if tool is None:
            raise ValueError(f"Tool not found: {tool_name}")
        
        logger.info(f"Executing tool: {tool_name}")
        result = await tool.execute(input_data)
        return result


# Global registry instance
_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


def init_registry() -> ToolRegistry:
    """Initialize tool registry with all tools.
    
    Returns:
        Initialized registry
    """
    registry = get_registry()
    
    if registry._initialized:
        logger.warning("Registry already initialized")
        return registry
    
    # Register browser tools
    for tool in get_all_browser_tools():
        registry.register(tool)
    
    registry._initialized = True
    logger.info(f"Initialized registry with {len(registry.get_all())} tools")
    
    return registry


def reset_registry() -> None:
    """Reset the global registry."""
    global _registry
    _registry = None
    logger.info("Registry reset")