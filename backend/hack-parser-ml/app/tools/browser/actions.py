"""Browser Actions - Action handlers for MCP tools."""

from typing import Dict, Any, Optional
from app.mcp.models import MCPTool, ToolResult, ExecutionContext, ToolCategory
from app.browser.session_manager import get_browser_manager
from app.browser.browser_service import get_browser_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserOpenUrlTool(MCPTool):
    """Tool to open a URL in browser."""
    
    name = "browser.open_url"
    description = "Open a URL in the browser and wait for page load"
    category = ToolCategory.NAVIGATION
    tags = ["browser", "navigation", "page"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to open"},
            "wait_until": {
                "type": "string", 
                "enum": ["load", "domcontentloaded", "networkidle"],
                "default": "load"
            },
            "timeout": {"type": "number", "default": 120000},
        },
        "required": ["url"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "url": {"type": "string"},
            "title": {"type": "string"},
            "status": {"type": "number"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute open URL."""
        manager = get_browser_manager()
        browser_service = get_browser_service()
        
        # Create session if needed
        if context.session_id not in manager.get_active_sessions():
            await manager.create_session(context.session_id)
        
        try:
            result = await browser_service.open_url(
                session_id=context.session_id,
                url=input_data["url"],
                wait_until=input_data.get("wait_until", "load"),
                timeout=input_data.get("timeout", 120000),
            )
            
            return ToolResult(
                success=result.get("success", False),
                output={
                    "url": result.get("url"),
                    "title": result.get("title"),
                    "status": result.get("status"),
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserClickTool(MCPTool):
    """Tool to click an element."""
    
    name = "browser.click"
    description = "Click on an element identified by CSS selector"
    category = ToolCategory.INTERACTION
    tags = ["browser", "interaction", "click"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector to click"},
            "timeout": {"type": "number", "default": 20000},
        },
        "required": ["selector"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "selector": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute click."""
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.click(
                session_id=context.session_id,
                selector=input_data["selector"],
                timeout=input_data.get("timeout", 20000),
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserTypeTool(MCPTool):
    """Tool to type text into an element."""
    
    name = "browser.type"
    description = "Type text into an input field identified by CSS selector"
    category = ToolCategory.INTERACTION
    tags = ["browser", "interaction", "input"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector to type into"},
            "text": {"type": "string", "description": "Text to type"},
            "clear_first": {"type": "boolean", "default": True},
            "timeout": {"type": "number", "default": 20000},
        },
        "required": ["selector", "text"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "selector": {"type": "string"},
            "text_length": {"type": "number"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute type."""
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.type_text(
                session_id=context.session_id,
                selector=input_data["selector"],
                text=input_data["text"],
                clear_first=input_data.get("clear_first", True),
                timeout=input_data.get("timeout", 20000),
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserPressKeyTool(MCPTool):
    """Tool to press a keyboard key."""
    
    name = "browser.press"
    description = "Press a keyboard key (Enter, Escape, etc.)"
    category = ToolCategory.INTERACTION
    tags = ["browser", "interaction", "keyboard"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key to press (Enter, Escape, etc.)"},
        },
        "required": ["key"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "key": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute press key."""
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.press_key(
                session_id=context.session_id,
                key=input_data["key"],
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserScrollTool(MCPTool):
    """Tool to scroll the page."""
    
    name = "browser.scroll"
    description = "Scroll the page in a direction (up, down, top, bottom)"
    category = ToolCategory.INTERACTION
    tags = ["browser", "interaction", "scroll"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["up", "down", "top", "bottom"],
                "default": "down"
            },
            "amount": {"type": "number", "default": 500},
        },
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "direction": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute scroll."""
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.scroll(
                session_id=context.session_id,
                direction=input_data.get("direction", "down"),
                amount=input_data.get("amount", 500),
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserGoBackTool(MCPTool):
    """Tool to go back in browser history."""
    
    name = "browser.go_back"
    description = "Go back to previous page in browser history"
    category = ToolCategory.NAVIGATION
    tags = ["browser", "navigation"]
    
    input_schema = {
        "type": "object",
        "properties": {}
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "url": {"type": "string"},
            "title": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute go back."""
        manager = get_browser_manager()
        
        try:
            result = await manager.go_back(context.session_id)
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserGetUrlTool(MCPTool):
    """Tool to get current URL."""
    
    name = "browser.get_current_url"
    description = "Get the current URL of the browser page"
    category = ToolCategory.NAVIGATION
    tags = ["browser", "navigation", "read"]
    
    input_schema = {
        "type": "object",
        "properties": {}
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "url": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute get URL."""
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.get_current_url(context.session_id)
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserScreenshotTool(MCPTool):
    """Tool to take screenshot."""
    
    name = "browser.screenshot"
    description = "Take a screenshot of the current page"
    category = ToolCategory.NAVIGATION
    tags = ["browser", "screenshot", "capture"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Optional screenshot name"},
        },
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "path": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute screenshot."""
        manager = get_browser_manager()
        
        try:
            result = await manager.take_screenshot(
                session_id=context.session_id,
                name=input_data.get("name"),
            )
            return ToolResult(
                success=result.get("success", False),
                output=result,
                screenshot_path=result.get("path"),
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Export all tools
BROWSER_TOOLS = [
    BrowserOpenUrlTool(),
    BrowserClickTool(),
    BrowserTypeTool(),
    BrowserPressKeyTool(),
    BrowserScrollTool(),
    BrowserGoBackTool(),
    BrowserGetUrlTool(),
    BrowserScreenshotTool(),
]
