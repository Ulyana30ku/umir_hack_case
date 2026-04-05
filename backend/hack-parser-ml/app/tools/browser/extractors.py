"""Page Extractors - Extraction tools for MCP."""

from typing import Dict, Any
from app.mcp.models import MCPTool, ToolResult, ExecutionContext, ToolCategory
from app.browser.page_service import get_page_service
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserGetTextTool(MCPTool):
    """Tool to get page text content."""
    
    name = "browser.get_page_text"
    description = "Get the text content of the current page"
    category = ToolCategory.EXTRACTION
    tags = ["browser", "extraction", "text", "read"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "max_length": {"type": "number", "default": 10000},
        },
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "text": {"type": "string"},
            "text_length": {"type": "number"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute get text."""
        page_service = get_page_service()
        
        try:
            result = await page_service.get_text(
                session_id=context.session_id,
                max_length=input_data.get("max_length", 10000),
            )
            return ToolResult(
                success=result.get("success", False),
                output=result,
                html_snapshot=result.get("text"),
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserGetHtmlTool(MCPTool):
    """Tool to get page HTML."""
    
    name = "browser.get_page_html"
    description = "Get the HTML content of the current page"
    category = ToolCategory.EXTRACTION
    tags = ["browser", "extraction", "html", "read"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "max_length": {"type": "number", "default": 50000},
        },
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "html": {"type": "string"},
            "html_length": {"type": "number"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute get HTML."""
        page_service = get_page_service()
        
        try:
            result = await page_service.get_html(
                session_id=context.session_id,
                max_length=input_data.get("max_length", 50000),
            )
            return ToolResult(
                success=result.get("success", False),
                output=result,
                html_snapshot=result.get("html"),
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserGetLinksTool(MCPTool):
    """Tool to get all links on page."""
    
    name = "browser.get_links"
    description = "Get all links from the current page"
    category = ToolCategory.EXTRACTION
    tags = ["browser", "extraction", "links", "read"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "number", "default": 50},
        },
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "links": {"type": "array"},
            "count": {"type": "number"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute get links."""
        page_service = get_page_service()
        
        try:
            result = await page_service.get_links(
                session_id=context.session_id,
                limit=input_data.get("limit", 50),
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserGetTitleTool(MCPTool):
    """Tool to get page title."""
    
    name = "browser.get_title"
    description = "Get the title of the current page"
    category = ToolCategory.EXTRACTION
    tags = ["browser", "extraction", "title", "read"]
    
    input_schema = {
        "type": "object",
        "properties": {}
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "title": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute get title."""
        from app.browser.browser_service import get_browser_service
        browser_service = get_browser_service()
        
        try:
            page = browser_service.manager.get_page(context.session_id)
            if page is None:
                return ToolResult(success=False, error="Session not found")
            
            title = await page.title()
            return ToolResult(success=True, output={"title": title})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserWaitForSelectorTool(MCPTool):
    """Tool to wait for selector."""
    
    name = "browser.wait_for_selector"
    description = "Wait for a CSS selector to appear on the page"
    category = ToolCategory.WAIT
    tags = ["browser", "wait", "selector"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS selector to wait for"},
            "timeout": {"type": "number", "default": 30000},
        },
        "required": ["selector"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "found": {"type": "boolean"},
            "selector": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute wait for selector."""
        from app.browser.browser_service import get_browser_service
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.wait_for_selector(
                session_id=context.session_id,
                selector=input_data["selector"],
                timeout=input_data.get("timeout", 30000),
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class BrowserWaitForTextTool(MCPTool):
    """Tool to wait for text."""
    
    name = "browser.wait_for_text"
    description = "Wait for specific text to appear on the page"
    category = ToolCategory.WAIT
    tags = ["browser", "wait", "text"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to wait for"},
            "timeout": {"type": "number", "default": 30000},
        },
        "required": ["text"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "found": {"type": "boolean"},
            "text": {"type": "string"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute wait for text."""
        from app.browser.browser_service import get_browser_service
        browser_service = get_browser_service()
        
        try:
            result = await browser_service.wait_for_text(
                session_id=context.session_id,
                text=input_data["text"],
                timeout=input_data.get("timeout", 30000),
            )
            return ToolResult(success=result.get("success", False), output=result)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ExtractStructuredDataTool(MCPTool):
    """Tool to extract structured data from page."""
    
    name = "extract.structured_data"
    description = "Extract structured data from page using CSS selectors"
    category = ToolCategory.EXTRACTION
    tags = ["browser", "extraction", "structured", "data"]
    
    input_schema = {
        "type": "object",
        "properties": {
            "selectors": {
                "type": "object", 
                "description": "Map of field names to CSS selectors"
            },
        },
        "required": ["selectors"]
    }
    
    output_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "data": {"type": "object"},
            "error": {"type": "string"},
        }
    }
    
    async def execute(self, input_data: Dict[str, Any], context: ExecutionContext) -> ToolResult:
        """Execute extract structured data."""
        page_service = get_page_service()
        
        try:
            # Get all elements for each selector
            selectors = input_data.get("selectors", {})
            data = {}
            
            for field_name, selector in selectors.items():
                result = await page_service.extract_elements(
                    session_id=context.session_id,
                    selector=selector,
                )
                
                if result.get("success") and result.get("elements"):
                    # Take first element text
                    data[field_name] = result["elements"][0].get("text", "")
                else:
                    data[field_name] = None
            
            return ToolResult(success=True, output={"data": data})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


# Export all extraction tools
EXTRACTION_TOOLS = [
    BrowserGetTextTool(),
    BrowserGetHtmlTool(),
    BrowserGetLinksTool(),
    BrowserGetTitleTool(),
    BrowserWaitForSelectorTool(),
    BrowserWaitForTextTool(),
    ExtractStructuredDataTool(),
]
