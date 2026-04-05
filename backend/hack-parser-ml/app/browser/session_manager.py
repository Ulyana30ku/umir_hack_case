"""Browser Session Manager - Playwright lifecycle and session management."""

import asyncio
import uuid
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class BrowserSession:

    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    error_count: int = 0
    last_action: Optional[str] = None


class BrowserSessionManager:

    
    def __init__(self, headless: bool = True, artifacts_dir: str = "./artifacts"):

        self._headless = headless
        self._artifacts_dir = Path(artifacts_dir)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._sessions: Dict[str, BrowserSession] = {}
        self._contexts: Dict[str, BrowserContext] = {}
        self._pages: Dict[str, Page] = {}
        self._default_context: Optional[BrowserContext] = None
        self._initialized = False
        

        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    async def start(self) -> None:

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
                '--disable-setuid-sandbox',
                '--disable-web-security',
            ]
        )
        

        self._default_context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self._initialized = True
        logger.info("Browser started successfully")
    
    async def stop(self) -> None:

        logger.info("Stopping browser sessions")
        

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
        self._initialized = False
        
        logger.info("Browser stopped")
    
    async def create_session(self, session_id: Optional[str] = None) -> str:

        if not self._initialized:
            await self.start()
        
        if session_id is None:
            session_id = str(uuid.uuid4())
        

        context = await self._browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        

        page = await context.new_page()
        

        self._contexts[session_id] = context
        self._pages[session_id] = page
        self._sessions[session_id] = BrowserSession(session_id=session_id)
        
        logger.info(f"Created browser session: {session_id}")
        return session_id
    
    async def close_session(self, session_id: str) -> bool:

        if session_id not in self._sessions:
            logger.warning(f"Session not found: {session_id}")
            return False
        

        if session_id in self._pages:
            try:
                await self._pages[session_id].close()
            except Exception as e:
                logger.warning(f"Error closing page: {e}")
            del self._pages[session_id]
        

        if session_id in self._contexts:
            try:
                await self._contexts[session_id].close()
            except Exception as e:
                logger.warning(f"Error closing context: {e}")
            del self._contexts[session_id]
        

        del self._sessions[session_id]
        
        logger.info(f"Closed session: {session_id}")
        return True
    
    def get_page(self, session_id: str) -> Optional[Page]:

        return self._pages.get(session_id)
    
    def get_session(self, session_id: str) -> Optional[BrowserSession]:

        return self._sessions.get(session_id)
    
    def get_state(self, session_id: str) -> Dict[str, Any]:

        session = self._sessions.get(session_id)
        page = self._pages.get(session_id)
        
        if not session or not page:
            return {}
        
        return {
            "current_url": page.url,
            "page_title": session.page_title,
            "history": session.page_url,  # Single previous URL for now
            "error_count": session.error_count,
        }
    
    async def navigate(
        self, 
        session_id: str, 
        url: str, 
        wait_until: str = "load",
        timeout: int = 120000,
    ) -> Dict[str, Any]:

        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:

            session = self._sessions[session_id]
            if session.page_url:
                session.last_action = f"navigated_to:{session.page_url}"
            
            response = await page.goto(url, wait_until=wait_until, timeout=timeout)
            

            session.page_url = page.url
            session.page_title = await page.title()
            
            result = {
                "success": True,
                "url": page.url,
                "title": session.page_title,
                "status": response.status if response else None,
            }
            
            logger.info(f"Navigated to {url}: status={result.get('status')}")
            return result
            
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            if session_id in self._sessions:
                self._sessions[session_id].error_count += 1
            
            return {"success": False, "error": str(e)}
    
    async def go_back(self, session_id: str) -> Dict[str, Any]:

        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            response = await page.go_back()
            session = self._sessions.get(session_id)
            if session:
                session.page_url = page.url
                session.page_title = await page.title()
            
            return {
                "success": True,
                "url": page.url,
                "title": await page.title(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def reload(self, session_id: str) -> Dict[str, Any]:

        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            response = await page.reload()
            return {
                "success": True,
                "url": page.url,
                "status": response.status if response else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(
        self, 
        session_id: str, 
        name: Optional[str] = None,
    ) -> Dict[str, Any]:

        page = self.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            # Generate filename
            if name is None:
                name = f"screenshot_{session_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            path = self._artifacts_dir / f"{name}.png"
            

            await page.screenshot(path=str(path), full_page=False)
            
            logger.info(f"Screenshot saved: {path}")
            return {"success": True, "path": str(path)}
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return {"success": False, "error": str(e)}
    
    def is_initialized(self) -> bool:

        return self._initialized
    
    def get_active_sessions(self) -> List[str]:

        return list(self._sessions.keys())
    
    def get_session_count(self) -> int:

        return len(self._sessions)



_browser_manager: Optional[BrowserSessionManager] = None


def get_browser_manager() -> BrowserSessionManager:

    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserSessionManager()
    return _browser_manager


async def init_browser(headless: bool = True) -> BrowserSessionManager:

    manager = get_browser_manager()
    manager._headless = headless
    await manager.start()
    return manager


async def close_browser() -> None:

    manager = get_browser_manager()
    await manager.stop()
