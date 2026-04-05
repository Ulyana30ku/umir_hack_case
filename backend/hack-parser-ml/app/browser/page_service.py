"""Page Service - Page content extraction and reading."""

from typing import Optional, Dict, Any, List
from app.browser.session_manager import BrowserSessionManager, get_browser_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


class PageService:

    
    def __init__(self, manager: Optional[BrowserSessionManager] = None):

        self.manager = manager or get_browser_manager()
    
    async def get_text(
        self,
        session_id: str,
        max_length: int = 10000,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            text = await page.evaluate("document.body.innerText")

            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            logger.info(f"Got page text: {len(text)} chars")
            return {"success": True, "text": text, "text_length": len(text)}
        except Exception as e:
            logger.error(f"Get text error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_html(
        self,
        session_id: str,
        max_length: int = 50000,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            html = await page.content()

            if len(html) > max_length:
                html = html[:max_length] + "..."
            
            logger.info(f"Got page HTML: {len(html)} chars")
            return {"success": True, "html": html, "html_length": len(html)}
        except Exception as e:
            logger.error(f"Get HTML error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_links(
        self,
        session_id: str,
        limit: int = 50,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
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
            
            links = links[:limit]
            logger.info(f"Found {len(links)} links")
            return {"success": True, "links": links, "count": len(links)}
        except Exception as e:
            logger.error(f"Get links error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_images(
        self,
        session_id: str,
        limit: int = 20,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            images = await page.evaluate("""() => {
                const imgs = document.querySelectorAll('img');
                return Array.from(imgs).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.width,
                    height: img.height
                })).filter(i => i.src);
            }""")
            
            images = images[:limit]
            logger.info(f"Found {len(images)} images")
            return {"success": True, "images": images, "count": len(images)}
        except Exception as e:
            logger.error(f"Get images error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_metadata(self, session_id: str) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            metadata = await page.evaluate("""() => {
                const getMeta = (name) => {
                    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                    return el ? el.content : null;
                };
                return {
                    title: document.title,
                    description: getMeta('description'),
                    og_title: getMeta('og:title'),
                    og_description: getMeta('og:description'),
                    og_image: getMeta('og:image'),
                };
            }""")
            
            return {"success": True, **metadata}
        except Exception as e:
            logger.error(f"Get metadata error: {e}")
            return {"success": False, "error": str(e)}
    
    async def extract_elements(
        self,
        session_id: str,
        selector: str,
    ) -> Dict[str, Any]:

        page = self.manager.get_page(session_id)
        if page is None:
            return {"success": False, "error": "Session not found"}
        
        try:
            elements = await page.query_selector_all(selector)
            results = []
            
            for el in elements:
                text = await el.inner_text()
                html = await el.evaluate("el => el.outerHTML")
                results.append({
                    "text": text.strip()[:200],
                    "html": html[:500],
                })
            
            logger.info(f"Extracted {len(results)} elements for {selector}")
            return {"success": True, "elements": results, "count": len(results)}
        except Exception as e:
            logger.error(f"Extract elements error: {e}")
            return {"success": False, "error": str(e)}



_page_service: Optional[PageService] = None


def get_page_service() -> PageService:

    global _page_service
    if _page_service is None:
        _page_service = PageService()
    return _page_service
