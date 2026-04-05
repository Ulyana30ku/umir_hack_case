"""Browser automation tools."""

import uuid
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from app.tools.browser.base import BaseTool
from app.tools.browser.session import get_browser_manager


# ============ Input/Output Schemas ============

class BrowserOpenUrlInput(BaseModel):
    """Input for browser_open_url tool."""
    url: str = Field(..., description="URL to open")
    wait_until: str = Field(default="load", description="Wait until event (load, domcontentloaded, networkidle)")


class BrowserOpenUrlOutput(BaseModel):
    """Output for browser_open_url tool."""
    success: bool
    url: Optional[str] = None
    title: Optional[str] = None
    status: Optional[int] = None
    error: Optional[str] = None


class BrowserClickInput(BaseModel):
    """Input for browser_click tool."""
    session_id: str = Field(..., description="Browser session ID")
    selector: str = Field(..., description="CSS selector to click")
    timeout: int = Field(default=5000, description="Timeout in milliseconds")


class BrowserClickOutput(BaseModel):
    """Output for browser_click tool."""
    success: bool
    selector: Optional[str] = None
    error: Optional[str] = None


class BrowserTypeInput(BaseModel):
    """Input for browser_type tool."""
    session_id: str = Field(..., description="Browser session ID")
    selector: str = Field(..., description="CSS selector to type into")
    text: str = Field(..., description="Text to type")
    clear_first: bool = Field(default=True, description="Clear existing text first")


class BrowserTypeOutput(BaseModel):
    """Output for browser_type tool."""
    success: bool
    selector: Optional[str] = None
    text_length: Optional[int] = None
    error: Optional[str] = None


class BrowserScrollInput(BaseModel):
    """Input for browser_scroll tool."""
    session_id: str = Field(..., description="Browser session ID")
    direction: str = Field(default="down", description="Scroll direction (up, down, top, bottom)")
    amount: int = Field(default=500, description="Scroll amount in pixels")


class BrowserScrollOutput(BaseModel):
    """Output for browser_scroll tool."""
    success: bool
    direction: Optional[str] = None
    error: Optional[str] = None


class BrowserWaitTextInput(BaseModel):
    """Input for browser_wait_for_text tool."""
    session_id: str = Field(..., description="Browser session ID")
    text: str = Field(..., description="Text to wait for")
    timeout: int = Field(default=10000, description="Timeout in milliseconds")


class BrowserWaitTextOutput(BaseModel):
    """Output for browser_wait_for_text tool."""
    success: bool
    found: Optional[bool] = None
    error: Optional[str] = None


class BrowserGetTextInput(BaseModel):
    """Input for browser_get_page_text tool."""
    session_id: str = Field(..., description="Browser session ID")


class BrowserGetTextOutput(BaseModel):
    """Output for browser_get_page_text tool."""
    success: bool
    text: Optional[str] = None
    text_length: Optional[int] = None
    error: Optional[str] = None


class BrowserGetHtmlInput(BaseModel):
    """Input for browser_get_page_html tool."""
    session_id: str = Field(..., description="Browser session ID")


class BrowserGetHtmlOutput(BaseModel):
    """Output for browser_get_page_html tool."""
    success: bool
    html: Optional[str] = None
    html_length: Optional[int] = None
    error: Optional[str] = None


class BrowserGetLinksInput(BaseModel):
    """Input for browser_get_links tool."""
    session_id: str = Field(..., description="Browser session ID")


class BrowserGetLinksOutput(BaseModel):
    """Output for browser_get_links tool."""
    success: bool
    links: Optional[List[Dict[str, str]]] = None
    count: Optional[int] = None
    error: Optional[str] = None


class BrowserGetUrlInput(BaseModel):
    """Input for browser_get_current_url tool."""
    session_id: str = Field(..., description="Browser session ID")


class BrowserGetUrlOutput(BaseModel):
    """Output for browser_get_current_url tool."""
    success: bool
    url: Optional[str] = None
    error: Optional[str] = None


class BrowserScreenshotInput(BaseModel):
    """Input for browser_screenshot tool."""
    session_id: str = Field(..., description="Browser session ID")
    path: Optional[str] = Field(default=None, description="Path to save screenshot")


class BrowserScreenshotOutput(BaseModel):
    """Output for browser_screenshot tool."""
    success: bool
    path: Optional[str] = None
    error: Optional[str] = None


class BrowserGoBackInput(BaseModel):
    """Input for browser_go_back tool."""
    session_id: str = Field(..., description="Browser session ID")


class BrowserGoBackOutput(BaseModel):
    """Output for browser_go_back tool."""
    success: bool
    error: Optional[str] = None


class ExtractDataInput(BaseModel):
    """Input for extract_structured_data tool."""
    session_id: str = Field(..., description="Browser session ID")
    selectors: Dict[str, str] = Field(..., description="Map of field names to CSS selectors")


class ExtractDataOutput(BaseModel):
    """Output for extract_structured_data tool."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============ Tool Implementations ============

class BrowserOpenUrlTool(BaseTool):
    """Tool to open a URL in browser."""
    
    def __init__(self):
        super().__init__(
            name="browser_open_url",
            description="Open a URL in the browser and wait for page load"
        )
    
    @property
    def input_schema(self):
        return BrowserOpenUrlInput
    
    @property
    def output_schema(self):
        return BrowserOpenUrlOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        
        # Create new session if needed
        session_id = str(uuid.uuid4())
        await manager.create_session(session_id)
        
        # Navigate
        result = await manager.navigate(session_id, input_data["url"], input_data.get("wait_until", "load"))
        
        # Update result with session_id
        result["session_id"] = session_id
        return result


class BrowserClickTool(BaseTool):
    """Tool to click an element."""
    
    def __init__(self):
        super().__init__(
            name="browser_click",
            description="Click on an element identified by CSS selector"
        )
    
    @property
    def input_schema(self):
        return BrowserClickInput
    
    @property
    def output_schema(self):
        return BrowserClickOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        return await manager.click(
            input_data["session_id"],
            input_data["selector"],
            input_data.get("timeout", 5000)
        )


class BrowserTypeTool(BaseTool):
    """Tool to type text into an element."""
    
    def __init__(self):
        super().__init__(
            name="browser_type",
            description="Type text into an input field identified by CSS selector"
        )
    
    @property
    def input_schema(self):
        return BrowserTypeInput
    
    @property
    def output_schema(self):
        return BrowserTypeOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        result = await manager.type_text(
            input_data["session_id"],
            input_data["selector"],
            input_data["text"],
            input_data.get("clear_first", True)
        )
        if result.get("success"):
            result["text_length"] = len(input_data["text"])
        return result


class BrowserScrollTool(BaseTool):
    """Tool to scroll the page."""
    
    def __init__(self):
        super().__init__(
            name="browser_scroll",
            description="Scroll the page in a direction (up, down, top, bottom)"
        )
    
    @property
    def input_schema(self):
        return BrowserScrollInput
    
    @property
    def output_schema(self):
        return BrowserScrollOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        return await manager.scroll(
            input_data["session_id"],
            input_data.get("direction", "down"),
            input_data.get("amount", 500)
        )


class BrowserWaitTextTool(BaseTool):
    """Tool to wait for text on page."""
    
    def __init__(self):
        super().__init__(
            name="browser_wait_for_text",
            description="Wait for specific text to appear on the page"
        )
    
    @property
    def input_schema(self):
        return BrowserWaitTextInput
    
    @property
    def output_schema(self):
        return BrowserWaitTextOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        return await manager.wait_for_text(
            input_data["session_id"],
            input_data["text"],
            input_data.get("timeout", 10000)
        )


class BrowserGetTextTool(BaseTool):
    """Tool to get page text."""
    
    def __init__(self):
        super().__init__(
            name="browser_get_page_text",
            description="Get the text content of the current page"
        )
    
    @property
    def input_schema(self):
        return BrowserGetTextInput
    
    @property
    def output_schema(self):
        return BrowserGetTextOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        result = await manager.get_page_text(input_data["session_id"])
        if result.get("success"):
            result["text_length"] = len(result.get("text", ""))
        return result


class BrowserGetHtmlTool(BaseTool):
    """Tool to get page HTML."""
    
    def __init__(self):
        super().__init__(
            name="browser_get_page_html",
            description="Get the HTML content of the current page"
        )
    
    @property
    def input_schema(self):
        return BrowserGetHtmlInput
    
    @property
    def output_schema(self):
        return BrowserGetHtmlOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        result = await manager.get_page_html(input_data["session_id"])
        if result.get("success"):
            result["html_length"] = len(result.get("html", ""))
        return result


class BrowserGetLinksTool(BaseTool):
    """Tool to get all links on page."""
    
    def __init__(self):
        super().__init__(
            name="browser_get_links",
            description="Get all links from the current page"
        )
    
    @property
    def input_schema(self):
        return BrowserGetLinksInput
    
    @property
    def output_schema(self):
        return BrowserGetLinksOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        result = await manager.get_links(input_data["session_id"])
        if result.get("success"):
            result["count"] = len(result.get("links", []))
        return result


class BrowserGetUrlTool(BaseTool):
    """Tool to get current URL."""
    
    def __init__(self):
        super().__init__(
            name="browser_get_current_url",
            description="Get the current URL of the browser page"
        )
    
    @property
    def input_schema(self):
        return BrowserGetUrlInput
    
    @property
    def output_schema(self):
        return BrowserGetUrlOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        return await manager.get_current_url(input_data["session_id"])


class BrowserScreenshotTool(BaseTool):
    """Tool to take screenshot."""
    
    def __init__(self):
        super().__init__(
            name="browser_screenshot",
            description="Take a screenshot of the current page"
        )
    
    @property
    def input_schema(self):
        return BrowserScreenshotInput
    
    @property
    def output_schema(self):
        return BrowserScreenshotOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        return await manager.screenshot(
            input_data["session_id"],
            input_data.get("path")
        )


class BrowserGoBackTool(BaseTool):
    """Tool to go back in browser history."""
    
    def __init__(self):
        super().__init__(
            name="browser_go_back",
            description="Go back to previous page in browser history"
        )
    
    @property
    def input_schema(self):
        return BrowserGoBackInput
    
    @property
    def output_schema(self):
        return BrowserGoBackOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        return await manager.go_back(input_data["session_id"])


class ExtractStructuredDataTool(BaseTool):
    """Tool to extract structured data from page."""
    
    def __init__(self):
        super().__init__(
            name="extract_structured_data",
            description="Extract structured data from page using CSS selectors"
        )
    
    @property
    def input_schema(self):
        return ExtractDataInput
    
    @property
    def output_schema(self):
        return ExtractDataOutput
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        manager = get_browser_manager()
        page = manager.get_page(input_data["session_id"])
        
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            data = {}
            for field_name, selector in input_data["selectors"].items():
                elements = await page.query_selector_all(selector)
                if len(elements) == 1:
                    data[field_name] = await elements[0].inner_text()
                else:
                    data[field_name] = [await el.inner_text() for el in elements]
            
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}


# ============ Registry ============

def get_all_browser_tools() -> List[BaseTool]:
    """Get all browser tools."""
    return [
        BrowserOpenUrlTool(),
        BrowserClickTool(),
        BrowserTypeTool(),
        BrowserScrollTool(),
        BrowserWaitTextTool(),
        BrowserGetTextTool(),
        BrowserGetHtmlTool(),
        BrowserGetLinksTool(),
        BrowserGetUrlTool(),
        BrowserScreenshotTool(),
        BrowserGoBackTool(),
        ExtractStructuredDataTool(),
    ]