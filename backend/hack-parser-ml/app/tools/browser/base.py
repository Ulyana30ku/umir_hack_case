"""Base classes for tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """Base class for tool input schemas."""
    pass


class ToolOutput(BaseModel):
    """Base class for tool output schemas."""
    success: bool = True
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str):
        """Initialize tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with input data.
        
        Args:
            input_data: Tool input data
            
        Returns:
            Tool output data
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for registry.
        
        Returns:
            Dict with tool schema
        """
        return {
            "name": self.name,
            "description": self.description,
        }
    
    @property
    @abstractmethod
    def input_schema(self) -> Optional[type[BaseModel]]:
        """Get input schema type."""
        pass
    
    @property
    @abstractmethod
    def output_schema(self) -> Optional[type[BaseModel]]:
        """Get output schema type."""
        pass