"""RSS News source integration."""

import asyncio
import re
from typing import Optional, List
from datetime import datetime
from xml.etree import ElementTree

import httpx

from app.integrations.news.base import BaseNewsSource
from app.schemas.news import NewsItem, NewsSearchResult
from app.schemas.query import NewsTask
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


def _get_rss_feeds() -> dict:
    """Get RSS feeds from settings or defaults."""
    feeds = {}
    
    if settings.news_source_1:
        feeds["iXBT"] = settings.news_source_1
    if settings.news_source_2:
        feeds["3DNews"] = settings.news_source_2
    if settings.news_source_3:
        feeds["Habr"] = settings.news_source_3
    if settings.news_source_4:
        feeds["Nplus1"] = settings.news_source_4
    
    # Fallback to defaults if none configured
    if not feeds:
        feeds = {
            "iXBT": "https://www.ixbt.com/rss/news.xml",
            "3DNews": "https://3dnews.ru/news/rss",
            "Habr": "https://habr.com/ru/rss/news/",
            "Nplus1": "https://nplus1.ru/rss",
        }
    
    return feeds


class RSSNewsSource(BaseNewsSource):
    """RSS News source for tech news with multiple feeds."""
    
    def __init__(self):
        """Initialize RSS news source."""
        self._feeds = _get_rss_feeds()
        self._client = httpx.AsyncClient(timeout=10.0, follow_redirects=True)
        logger.info(f"RSS News initialized with feeds: {list(self._feeds.keys())}")
    
    @property
    def name(self) -> str:
        """News source name."""
        return "RSS TechNews"
    
    async def search_news(
        self,
        task: NewsTask,
    ) -> NewsSearchResult:
        """Search for news using RSS feeds."""
        logger.info(f"Searching RSS news for: {task.topic}")
        
        # Try to fetch from RSS feeds - NO MOCK FALLBACK
        news_items = await self._fetch_rss_feeds(task.topic, task.limit)
        
        # If all feeds fail, return empty result (no mock data)
        if not news_items:
            logger.warning("All RSS feeds failed, returning empty result")
        
        return NewsSearchResult(
            news=news_items,
            total_found=len(news_items),
            search_topic=task.topic,
        )
    
    async def _fetch_rss_feeds(self, topic: str, limit: int) -> List[NewsItem]:
        """Fetch from RSS feeds with failover."""
        all_news_items = []
        failed_feeds = []
        
        for source_name, feed_url in self._feeds.items():
            try:
                logger.debug(f"Fetching {source_name} from {feed_url}")
                response = await self._client.get(feed_url)
                
                if response.status_code == 200:
                    items = self._parse_feed(response.text, source_name, topic)
                    all_news_items.extend(items)
                    logger.info(f"Fetched {len(items)} items from {source_name}")
                else:
                    failed_feeds.append(source_name)
                    logger.warning(f"Failed to fetch {source_name}: HTTP {response.status_code}")
                    
            except httpx.TimeoutException:
                failed_feeds.append(source_name)
                logger.warning(f"Timeout fetching {source_name}")
            except httpx.RequestError as e:
                failed_feeds.append(source_name)
                logger.warning(f"Request error for {source_name}: {e}")
            except Exception as e:
                failed_feeds.append(source_name)
                logger.warning(f"Failed to fetch {source_name}: {e}")
        
        if failed_feeds:
            logger.info(f"Failed feeds: {failed_feeds}, successful items: {len(all_news_items)}")
        
        # Sort by relevance and date (handle None dates)
        all_news_items.sort(key=lambda n: (
            -n.relevance_score,
            n.published_at.replace(tzinfo=None) if n.published_at and n.published_at.tzinfo else n.published_at or datetime.min,
        ))
        return all_news_items[:limit]
    
    def _parse_feed(self, xml_content: str, source: str, topic: str) -> List[NewsItem]:
        """Parse RSS/Atom feed content."""
        news_items = []
        
        try:
            # Try RSS first
            root = ElementTree.fromstring(xml_content)
            
            # Check if it's RSS or Atom
            if root.tag == "rss":
                news_items = self._parse_rss(root, source, topic)
            elif root.tag == "feed":  # Atom
                news_items = self._parse_atom(root, source, topic)
            else:
                # Try finding items anywhere
                for item in root.findall(".//item"):
                    news_items.extend(self._parse_rss_item(item, source, topic))
                    
        except ElementTree.ParseError as e:
            logger.warning(f"Failed to parse XML from {source}: {e}")
        except Exception as e:
            logger.warning(f"Error parsing feed from {source}: {e}")
        
        return news_items
    
    def _parse_rss(self, root, source: str, topic: str) -> List[NewsItem]:
        """Parse RSS feed."""
        items = root.findall(".//item")
        return [self._parse_rss_item(item, source, topic) for item in items]
    
    def _parse_rss_item(self, item, source: str, topic: str) -> Optional[NewsItem]:
        """Parse single RSS item."""
        try:
            title_elem = item.find("title")
            link_elem = item.find("link")
            desc_elem = item.find("description")
            pub_date_elem = item.find("pubDate")
            
            if title_elem is None or not title_elem.text:
                return None
            
            title = title_elem.text.strip()
            url = link_elem.text if link_elem is not None and link_elem.text else ""
            
            # Get description/summary
            snippet = ""
            if desc_elem is not None and desc_elem.text:
                # Clean HTML tags from description
                snippet = re.sub(r'<[^>]+>', '', desc_elem.text)[:200]
            
            # Parse date
            published_at = self._parse_date(pub_date_elem.text if pub_date_elem is not None and pub_date_elem.text else None)
            
            # Calculate relevance
            relevance = self._calculate_relevance(title, topic)
            
            return NewsItem(
                id=f"rss-{source}-{hash(title) % 100000}",
                title=title,
                source=source,
                published_at=published_at,
                url=url,
                snippet=snippet,
                topic=topic,
                relevance_score=relevance,
            )
        except Exception as e:
            logger.warning(f"Failed to parse RSS item: {e}")
            return None
    
    def _parse_atom(self, root, source: str, topic: str) -> List[NewsItem]:
        """Parse Atom feed."""
        items = root.findall(".//entry")
        result = []
        
        for entry in items:
            try:
                title_elem = entry.find("title")
                link_elem = entry.find("link")
                summary_elem = entry.find("summary") or entry.find("content")
                published_elem = entry.find("published") or entry.find("updated")
                
                if title_elem is None or not title_elem.text:
                    continue
                
                title = title_elem.text.strip()
                url = ""
                if link_elem is not None:
                    href = link_elem.get("href")
                    if href:
                        url = href
                
                snippet = ""
                if summary_elem is not None and summary_elem.text:
                    snippet = re.sub(r'<[^>]+>', '', summary_elem.text)[:200]
                
                published_at = self._parse_date(published_elem.text if published_elem is not None and published_elem.text else None)
                relevance = self._calculate_relevance(title, topic)
                
                result.append(NewsItem(
                    id=f"atom-{source}-{hash(title) % 100000}",
                    title=title,
                    source=source,
                    published_at=published_at,
                    url=url,
                    snippet=snippet,
                    topic=topic,
                    relevance_score=relevance,
                ))
            except Exception as e:
                logger.warning(f"Failed to parse Atom entry: {e}")
        
        return result
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse various date formats."""
        if not date_str:
            return None
        
        # First try parsing with timezone, then without
        # Remove timezone info from string if present to get naive datetime
        date_str_clean = date_str.strip()
        
        # Check if has timezone
        has_tz = any(tz in date_str_clean for tz in ['+', '-', 'Z', 'GMT', 'MSK'])
        
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",      # RFC 822 with timezone
            "%Y-%m-%dT%H:%M:%S%z",           # ISO 8601 with timezone
            "%Y-%m-%dT%H:%M:%S.%f%z",        # ISO 8601 with microseconds and timezone
            "%a, %d %b %Y %H:%M:%S",          # RFC 822 without timezone
            "%Y-%m-%dT%H:%M:%S",              # ISO 8601 without timezone
            "%Y-%m-%dT%H:%M:%S.%f",          # ISO 8601 with microseconds, no timezone
            "%Y-%m-%d %H:%M:%S",               # Simple datetime
            "%d %b %Y %H:%M:%S",              # Without timezone
            "%Y-%m-%d",                       # Date only
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str_clean, fmt)
                # If we parsed a timezone-aware format but Python made it naive,
                # that's fine - we'll compare naively
                return dt
            except:
                continue
        
        return None
    
    def _calculate_relevance(self, title: str, topic: str) -> float:
        """Calculate relevance score for a news item."""
        title_lower = title.lower()
        topic_lower = topic.lower()
        
        # Direct match
        if topic_lower in title_lower:
            return 0.9
        
        # Check for keywords
        keywords = [topic_lower]
        if "apple" in topic_lower or "iphone" in topic_lower:
            keywords.extend(["apple", "iphone", "ios", "mac", "ipad"])
        elif "samsung" in topic_lower:
            keywords.extend(["samsung", "galaxy", "android"])
        elif "google" in topic_lower:
            keywords.extend(["google", "pixel", "android"])
        
        if any(kw in title_lower for kw in keywords):
            return 0.7
        
        return 0.3
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


# Singleton instance
_news_source: Optional[RSSNewsSource] = None


def get_rss_news_source() -> RSSNewsSource:
    """Get RSS news source singleton."""
    global _news_source
    if _news_source is None:
        _news_source = RSSNewsSource()
    return _news_source