"""Browser automation module - Playwright-based session management."""

from app.browser.session_manager import BrowserSessionManager, get_browser_manager, init_browser, close_browser
from app.browser.browser_service import BrowserService
from app.browser.page_service import PageService
from app.browser.errors import (
    BrowserError,
    NavigationError,
    ElementNotFoundError,
    ElementNotVisibleError,
    TimeoutError as BrowserTimeoutError,
    InvalidSelectorError,
    BrowserClosedError,
    SessionNotFoundError,
    JavaScriptError,
    ScreenshotError,
    DownloadError,
)

__all__ = [
    "BrowserSessionManager",
    "get_browser_manager",
    "init_browser",
    "close_browser",
    "BrowserService",
    "PageService",
    "BrowserError",
    "NavigationError",
    "ElementNotFoundError",
    "ElementNotVisibleError",
    "BrowserTimeoutError",
    "InvalidSelectorError",
    "BrowserClosedError",
    "SessionNotFoundError",
    "JavaScriptError",
    "ScreenshotError",
    "DownloadError",
]
