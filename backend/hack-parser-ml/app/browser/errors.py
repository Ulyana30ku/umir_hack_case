"""Browser errors - Custom exceptions for browser automation."""

from typing import Optional


class BrowserError(Exception):

    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NavigationError(BrowserError):

    def __init__(self, message: str, url: Optional[str] = None, status_code: Optional[int] = None):
        details = {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)
        self.url = url
        self.status_code = status_code


class ElementNotFoundError(BrowserError):

    def __init__(self, selector: str, reason: Optional[str] = None):
        details = {"selector": selector}
        if reason:
            details["reason"] = reason
        super().__init__(f"Element not found: {selector}", details)
        self.selector = selector


class ElementNotVisibleError(BrowserError):

    def __init__(self, selector: str):
        super().__init__(f"Element not visible: {selector}", {"selector": selector})
        self.selector = selector


class TimeoutError(BrowserError):

    def __init__(self, operation: str, timeout_ms: int):
        super().__init__(
            f"Operation '{operation}' timed out after {timeout_ms}ms",
            {"operation": operation, "timeout_ms": timeout_ms}
        )
        self.operation = operation
        self.timeout_ms = timeout_ms


class InvalidSelectorError(BrowserError):

    def __init__(self, selector: str):
        super().__init__(f"Invalid selector: {selector}", {"selector": selector})
        self.selector = selector


class BrowserClosedError(BrowserError):

    def __init__(self, session_id: Optional[str] = None):
        details = {}
        if session_id:
            details["session_id"] = session_id
        super().__init__("Browser is closed", details)
        self.session_id = session_id


class SessionNotFoundError(BrowserError):

    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", {"session_id": session_id})
        self.session_id = session_id


class JavaScriptError(BrowserError):

    def __init__(self, script: str, error: str):
        super().__init__(f"JavaScript error: {error}", {"script": script, "error": error})
        self.script = script
        self.error = error


class ScreenshotError(BrowserError):

    def __init__(self, reason: str):
        super().__init__(f"Screenshot failed: {reason}", {"reason": reason})


class DownloadError(BrowserError):

    def __init__(self, url: str, reason: str):
        super().__init__(f"Download failed for {url}: {reason}", {"url": url, "reason": reason})
        self.url = url



Timeout = TimeoutError
