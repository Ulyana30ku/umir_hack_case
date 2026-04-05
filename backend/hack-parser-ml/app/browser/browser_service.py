"""Browser Service - High-level browser operations."""

from typing import Optional, Dict, Any, List
from app.browser.session_manager import BrowserSessionManager, get_browser_manager
from app.browser.errors import (
    NavigationError,
    ElementNotFoundError,
    TimeoutError as BrowserTimeoutError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserService:

    
    def __init__(self, manager: Optional[BrowserSessionManager] = None):

        self.manager = manager or get_browser_manager()
    
    async def open_url(
        self,
        session_id: str,
        url: str,
        wait_until: str = "load",
        timeout: int = 120000,
    ) -> Dict[str, Any]:

        result = await self.manager.navigate(session_id, url, wait_until, timeout)
        
        if not result.get("success"):
            raise NavigationError(
                f"Failed to navigate to {url}: {result.get('error')}",
                url=url,
            )
        
        return {
            "success": True,
            "url": result.get("url"),
            "title": result.get("title"),
            "status": result.get("status"),
        }
    
    async def click(
        self,
        session_id: str,
        selector: str,
        timeout: int = 20000,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            raise ElementNotFoundError(selector, "Session not found")
        
        try:
            await page.click(selector, timeout=timeout)
            logger.info(f"Clicked: {selector}")
            return {"success": True, "selector": selector}
        except Exception as e:
            logger.error(f"Click error: {e}")
            raise ElementNotFoundError(selector, str(e))
    
    async def type_text(
        self,
        session_id: str,
        selector: str,
        text: str,
        clear_first: bool = True,
        timeout: int = 20000,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            raise ElementNotFoundError(selector, "Session not found")
        
        try:
            if clear_first:
                await page.fill(selector, text)
            else:
                await page.type(selector, text)
            
            logger.info(f"Typed into {selector}: {text[:50]}...")
            return {"success": True, "selector": selector, "text_length": len(text)}
        except Exception as e:
            logger.error(f"Type error: {e}")
            raise ElementNotFoundError(selector, str(e))
    
    async def press_key(
        self,
        session_id: str,
        key: str,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            raise ElementNotFoundError("page", "Session not found")
        
        try:
            await page.keyboard.press(key)
            logger.info(f"Pressed key: {key}")
            return {"success": True, "key": key}
        except Exception as e:
            logger.error(f"Press key error: {e}")
            return {"success": False, "error": str(e)}
    
    async def scroll(
        self,
        session_id: str,
        direction: str = "down",
        amount: int = 500,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            raise ElementNotFoundError("page", "Session not found")
        
        try:
            if direction == "top":
                await page.evaluate("window.scrollTo(0, 0)")
            elif direction == "bottom":
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            elif direction == "up":
                await page.evaluate(f"window.scrollBy(0, -{amount})")
            else:  # down
                await page.evaluate(f"window.scrollBy(0, {amount})")
            
            logger.info(f"Scrolled {direction}")
            return {"success": True, "direction": direction, "amount": amount}
        except Exception as e:
            logger.error(f"Scroll error: {e}")
            return {"success": False, "error": str(e)}
    
    async def hover(
        self,
        session_id: str,
        selector: str,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            raise ElementNotFoundError(selector, "Session not found")
        
        try:
            await page.hover(selector)
            logger.info(f"Hovered: {selector}")
            return {"success": True, "selector": selector}
        except Exception as e:
            logger.error(f"Hover error: {e}")
            raise ElementNotFoundError(selector, str(e))
    
    async def select_option(
        self,
        session_id: str,
        selector: str,
        value: str,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            raise ElementNotFoundError(selector, "Session not found")
        
        try:
            await page.select_option(selector, value)
            logger.info(f"Selected option: {value} in {selector}")
            return {"success": True, "selector": selector, "value": value}
        except Exception as e:
            logger.error(f"Select option error: {e}")
            raise ElementNotFoundError(selector, str(e))
    
    async def wait_for_selector(
        self,
        session_id: str,
        selector: str,
        timeout: int = 30000,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"Found selector: {selector}")
            return {"success": True, "found": True, "selector": selector}
        except Exception as e:
            logger.warning(f"Selector not found: {selector}, error: {e}")
            return {"success": True, "found": False, "selector": selector, "error": str(e)}
    
    async def wait_for_text(
        self,
        session_id: str,
        text: str,
        timeout: int = 30000,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.wait_for_timeout(500)  # Small delay
            content = await page.evaluate("document.body.innerText")
            found = text in content
            
            logger.info(f"Wait for text '{text[:50]}...': {found}")
            return {"success": True, "found": found, "text": text}
        except Exception as e:
            logger.error(f"Wait for text error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_current_url(self, session_id: str) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        return {"success": True, "url": page.url}
    
    async def get_title(self, session_id: str) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        title = await page.title()
        return {"success": True, "title": title}



_browser_service: Optional[BrowserService] = None


def get_browser_service() -> BrowserService:

    global _browser_service
    if _browser_service is None:
        _browser_service = BrowserService()
    return _browser_service
