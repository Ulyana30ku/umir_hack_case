"""Browser automation layer with Playwright."""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BrowserSession:
    """Represents a browser session."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    error_count: int = 0
    
    
class BrowserSessionManager:
    """Manages Playwright browser sessions."""
    
    def __init__(self, headless: bool = True):
        """Initialize browser session manager.
        
        Args:
            headless: Run browser in headless mode
        """
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._sessions: Dict[str, BrowserSession] = {}
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        self._default_context: Optional[BrowserContext] = None
    
    async def start(self) -> None:
        """Start Playwright and create browser instance."""
        if self._browser is not None:
            logger.warning("Browser already started")
            return
            
        logger.info(f"Starting Playwright (headless={self._headless})")
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        
        # Create default context
        self._default_context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        logger.info("Browser started successfully")
    
    async def stop(self) -> None:
        """Stop Playwright and close all sessions."""
        logger.info("Stopping browser sessions")
        
        # Close all pages and contexts
        for page in self._pages.values():
            try:
                await page.close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
        
        for context in self._contexts.values():
            try:
                await context.close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
        
        if self._default_context:
            try:
                await self._default_context.close()
            except Exception as e:
                logger.warning(f"Error closing default context: {e}")
        
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning(f"Error stopping playwright: {e}")
        
        self._sessions.clear()
        self._pages.clear()
        self._contexts.clear()
        self._default_context = None
        self._browser = None
        self._playwright = None
        
        logger.info("Browser stopped")
    
    async def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new browser session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            
        Returns:
            Session ID
        """
        if self._browser is None:
            await self.start()
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        # Create new context for this session
        context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # Create new page
        page = await context.new_page()
        
        # Store references
        self._contexts[session_id] = context
        self._pages[session_id] = page
        self._sessions[session_id] = BrowserSession(session_id=session_id)
        
        logger.info(f"Created browser session: {session_id}")
        return session_id
    
    async def close_session(self, session_id: str) -> bool:
        """Close a browser session.
        
        Args:
            session_id: Session ID to close
            
        Returns:
            True if session was closed, False if not found
        """
        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        # Close page
        if session_id in self._pages:
            try:
                await self._pages[session_id].close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            del self._pages[session_id]
        
        # Close context
        if session_id in self._contexts:
            try:
                await self._contexts[session_id].close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
            del self._contexts[session_id]
        
        # Remove session
        del self._sessions[session_id]
        
        logger.info(f"Closed session: {session_id}")
        return True
    
    def get_page(self, session_id: str) -> Optional[Page]:
        """Get page for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Playwright Page or None
        """
        return self._pages.get(session_id)
    
    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Get session info.
        
        Args:
            session_id: Session ID
            
        Returns:
            BrowserSession or None
        """
        return self._sessions.get(session_id)
    
    async def navigate(self, session_id: str, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Navigate to URL.
        
        Args:
            session_id: Session ID
            url: URL to navigate to
            wait_until: Wait until event (load, domcontentloaded, networkidle)
            
        Returns:
            Dict with status, url, title
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Update session info
            if session_id in self._sessions:
                self._sessions[session_id].page_url = page.url
                self._sessions[session_id].page_title = await page.title()
            
            result = {
                "success": True,
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None,
            }
            
            logger.info(f"Navigated to {url}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            if session_id in self._sessions:
                self._sessions[session_id].error_count += 1
            
            return {"success": False, "error": str(e)}
    
    async def click(self, session_id: str, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        """Click element.
        
        Args:
            session_id: Session ID
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            Dict with success status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.click(selector, timeout=timeout)
            logger.info(f"Clicked: {selector}")
            return {"success": True, "selector": selector}
            
        except Exception as e:
            logger.error(f"Click error: {e}")
            return {"success": False, "error": str(e), "selector": selector}
    
    async def type_text(self, session_id: str, selector: str, text: str, 
                        clear_first: bool = True, timeout: int = 5000) -> Dict[str, Any]:
        """Type text into element.
        
        Args:
            session_id: Session ID
            selector: CSS selector
            text: Text to type
            clear_first: Clear existing text first
            timeout: Timeout in milliseconds
            
        Returns:
            Dict with success status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            if clear_first:
                await page.fill(selector, text)
            else:
                await page.type(selector, text)
            
            logger.info(f"Typed into {selector}: {text[:50]}...")
            return {"success": True, "selector": selector, "text": text}
            
        except Exception as e:
            logger.error(f"Type error: {e}")
            return {"success": False, "error": str(e), "selector": selector}
    
    async def press_key(self, session_id: str, key: str) -> Dict[str, Any]:
        """Press key.
        
        Args:
            session_id: Session ID
            key: Key to press (Enter, Escape, etc.)
            
        Returns:
            Dict with success status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.keyboard.press(key)
            logger.info(f"Pressed key: {key}")
            return {"success": True, "key": key}
            
        except Exception as e:
            logger.error(f"Press key error: {e}")
            return {"success": False, "error": str(e), "key": key}
    
    async def scroll(self, session_id: str, direction: str = "down", 
                     amount: int = 500) -> Dict[str, Any]:
        """Scroll page.
        
        Args:
            session_id: Session ID
            direction: scroll direction (up, down, top, bottom)
            amount: Scroll amount in pixels
            
        Returns:
            Dict with success status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
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
    
    async def wait_for_text(self, session_id: str, text: str, 
                            timeout: int = 10000) -> Dict[str, Any]:
        """Wait for text to appear on page.
        
        Args:
            session_id: Session ID
            text: Text to wait for
            timeout: Timeout in milliseconds
            
        Returns:
            Dict with found status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.wait_for_timeout(500)  # Small delay to let page settle
            content = await page.content()
            found = text in content
            
            logger.info(f"Wait for text '{text[:50]}...': {found}")
            return {"success": True, "found": found, "text": text}
            
        except Exception as e:
            logger.error(f"Wait for text error: {e}")
            return {"success": False, "error": str(e)}
    
    async def wait_for_selector(self, session_id: str, selector: str,
                                 timeout: int = 10000) -> Dict[str, Any]:
        """Wait for selector to appear.
        
        Args:
            session_id: Session ID
            selector: CSS selector
            timeout: Timeout in milliseconds
            
        Returns:
            Dict with found status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            logger.info(f"Found selector: {selector}")
            return {"success": True, "found": True, "selector": selector}
            
        except Exception as e:
            logger.warning(f"Selector not found: {selector}, error: {e}")
            return {"success": True, "found": False, "selector": selector, "error": str(e)}
    
    async def get_page_text(self, session_id: str) -> Dict[str, Any]:
        """Get page text content.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with text content
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            text = await page.evaluate("document.body.innerText")
            logger.info(f"Got page text: {len(text)} chars")
            return {"success": True, "text": text[:5000]}  # Limit size
            
        except Exception as e:
            logger.error(f"Get text error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_page_html(self, session_id: str) -> Dict[str, Any]:
        """Get page HTML.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with HTML content
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            html = await page.content()
            logger.info(f"Got page HTML: {len(html)} chars")
            return {"success": True, "html": html[:10000]}  # Limit size
            
        except Exception as e:
            logger.error(f"Get HTML error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_links(self, session_id: str) -> Dict[str, Any]:
        """Get all links on page.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with list of links
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            links = await page.evaluate("""() => {
                const anchors = document.querySelectorAll('a');
                return Array.from(anchors).map(a => ({
                    href: a.href,
                    text: a.innerText.trim().substring(0, 100)
                })).filter(l => l.href);
            }""")
            
            logger.info(f"Found {len(links)} links")
            return {"success": True, "links": links[:50]}  # Limit to 50
            
        except Exception as e:
            logger.error(f"Get links error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_current_url(self, session_id: str) -> Dict[str, Any]:
        """Get current URL.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with URL
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        return {"success": True, "url": page.url}
    
    async def screenshot(self, session_id: str, path: Optional[str] = None) -> Dict[str, Any]:
        """Take screenshot.
        
        Args:
            session_id: Session ID
            path: Optional path to save screenshot
            
        Returns:
            Dict with screenshot info
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            if path is None:
                path = f"screenshots/screenshot_{session_id}.png"
            
            await page.screenshot(path=path, full_page=True)
            logger.info(f"Screenshot saved: {path}")
            return {"success": True, "path": path}
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {"success": False, "error": str(e)}
    
    async def go_back(self, session_id: str) -> Dict[str, Any]:
        """Go back in browser history.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with success status
        """
        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            await page.go_back()
            logger.info("Went back")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"Go back error: {e}")
            return {"success": False, "error": str(e)}


# Global instance
_browser_manager: Optional[BrowserSessionManager] = None


def get_browser_manager() -> BrowserSessionManager:
    """Get global browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserSessionManager(headless=True)
    return _browser_manager


async def init_browser(headless: bool = True) -> None:
    """Initialize browser manager."""
    global _browser_manager
    _browser_manager = BrowserSessionManager(headless=headless)
    await _browser_manager.start()


async def close_browser() -> None:
    """Close browser manager."""
    global _browser_manager
    if _browser_manager:
        await _browser_manager.stop()
        _browser_manager = None