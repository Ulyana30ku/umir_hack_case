"""Query parser service for extracting structured tasks from natural language."""

import re
from typing import List, Optional

from app.schemas.query import ParsedUserQuery, ProductTask, NewsTask, IntentType, ExecutionHints
from app.utils.text import (
    normalize_memory,
    normalize_condition,
    extract_sort_order,
    extract_time_period,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Browser intent patterns
BROWSER_NAVIGATION_PATTERNS = [
    r'зайди\s+на\s+(\S+)',
    r'открой\s+сайт\s+(\S+)',
    r'открой\s+страницу\s+(\S+)',
    r'перейди\s+на\s+(\S+)',
    r'go\s+to\s+(\S+)',
    r'open\s+(\S+)',
]

BROWSER_INTERACTION_PATTERNS = [
    r'нажми',
    r'кликни',
    r'введи',
    r'напечатай',
    r'выбери',
    r'открой\s+(первый|второй|третий)',
    r'click',
    r'type',
    r'enter',
]

INFO_RETRIEVAL_PATTERNS = [
    r'верни\s+(заголовок|текст|цену|информацию)',
    r'получи\s+(текст|данные)',
    r'прочитай',
    r'скажи\s+что',
    r'что\s+(написано|есть)',
    r'верни\s+(url|ссылку)',
]

# Brand aliases for normalization
BRAND_ALIASES = {
    'apple': 'Apple',
    'iphone': 'Apple',  # iPhone implies Apple
    'samsung': 'Samsung',
    'galaxy': 'Samsung',
    'sony': 'Sony',
    'xiaomi': 'Xiaomi',
    'redmi': 'Xiaomi',
    'poco': 'Xiaomi',
    'huawei': 'Huawei',
    'google': 'Google',
    'pixel': 'Google',
    'oneplus': 'OnePlus',
    'oppo': 'OPPO',
    'vivo': 'Vivo',
    'motorola': 'Motorola',
}

# Category keywords
CATEGORY_KEYWORDS = {
    'смартфон': 'смартфон',
    'smartphone': 'смартфон',
    'phone': 'смартфон',
    'телефон': 'смартфон',
    'ноутбук': 'ноутбук',
    'laptop': 'ноутбук',
    'ноут': 'ноутбук',
    'планшет': 'планшет',
    'tablet': 'планшет',
    'наушники': 'наушники',
    'headphones': 'наушники',
    'часы': 'часы',
    'watch': 'часы',
}


class QueryParser:
    """Service for parsing user queries into structured tasks."""
    
    def __init__(self):
        """Initialize the query parser."""
        self._product_keywords = ['найди', 'найти', 'поиск', 'ищу', 'купить', 'подбери']
        self._news_keywords = ['новост', 'новости', 'news']
    
    def parse(self, query: str) -> ParsedUserQuery:
        """
        Parse user query into structured tasks.
        
        Uses hybrid approach:
        1. Rule-based normalization
        2. LLM-assisted extraction (if available)
        
        Args:
            query: Raw user query string
            
        Returns:
            ParsedUserQuery with extracted tasks
        """
        logger.info(f"Parsing query: {query}")
        
        # Step 1: Detect intent type (browser, product, news, multi-step)
        intent_type, execution_hints = self._detect_intent(query)
        
        # Step 2: Detect what tasks the query contains
        has_product_task = self._detect_product_task(query)
        has_news_task = self._detect_news_task(query)
        
        # Step 3: Extract product task if needed
        product_task = None
        if has_product_task:
            product_task = self._extract_product_task(query)
        
        # Step 4: Extract news task if needed
        news_task = None
        if has_news_task:
            news_task = self._extract_news_task(query)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(product_task, news_task)
        
        # Step 6: Detect ambiguities and assumptions
        ambiguities = self._detect_ambiguities(query, product_task, news_task)
        assumptions = self._make_assumptions(product_task, news_task)
        
        result = ParsedUserQuery(
            raw_query=query,
            normalized_query=query.strip(),
            intent_type=intent_type,
            execution_hints=execution_hints,
            product_task=product_task,
            news_task=news_task,
            ambiguities=ambiguities,
            assumptions=assumptions,
            confidence=confidence,
        )
        
        logger.info(f"Parsed query - intent: {intent_type}, confidence: {confidence}")
        return result
    
    def _detect_intent(self, query: str) -> tuple[IntentType, Optional[ExecutionHints]]:
        """Detect user intent type and extract execution hints."""
        query_lower = query.lower()
        hints = ExecutionHints()
        
        # Check for browser navigation
        for pattern in BROWSER_NAVIGATION_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                hints.target_url = match.group(1) if match.groups() else None
                return IntentType.BROWSER_NAVIGATION, hints
        
        # Check for browser interaction
        if any(re.search(p, query_lower) for p in BROWSER_INTERACTION_PATTERNS):
            # Extract button text or input text
            btn_match = re.search(r'нажми\s+(на\s+)?([\w\s]+)', query_lower)
            if btn_match:
                hints.button_text = btn_match.group(2).strip()
            
            input_match = re.search(r'введи\s+(.+?)(?:\s+в|\s+на)', query_lower)
            if input_match:
                hints.input_text = input_match.group(1).strip()
            
            return IntentType.BROWSER_INTERACTION, hints
        
        # Check for info retrieval
        if any(re.search(p, query_lower) for p in INFO_RETRIEVAL_PATTERNS):
            hints.requires_extraction = True
            return IntentType.INFO_RETRIEVAL, hints
        
        # Check for product search
        has_product = self._detect_product_task(query)
        has_news = self._detect_news_task(query)
        
        if has_product and has_news:
            hints.requires_multi_step_plan = True
            return IntentType.MULTI_STEP, hints
        elif has_product:
            hints.requires_browser = True
            hints.search_query = self._extract_search_query(query)
            return IntentType.PRODUCT_SEARCH, hints
        elif has_news:
            return IntentType.NEWS_SEARCH, hints
        
        # Default to browser interaction (user wants to do something in browser)
        return IntentType.BROWSER_INTERACTION, hints
    
    def _detect_product_task(self, query: str) -> bool:
        """Detect if query contains a product search task."""
        query_lower = query.lower()
        # Check for product keywords
        return any(kw in query_lower for kw in self._product_keywords)
        return any(kw in query_lower for kw in self._product_keywords)
    
    def _detect_news_task(self, query: str) -> bool:
        """Detect if query contains a news search task."""
        query_lower = query.lower()
        return any(kw in query_lower for kw in self._news_keywords)
    
    def _extract_product_task(self, query: str) -> Optional[ProductTask]:
        """Extract product search parameters from query."""
        query_lower = query.lower()
        
        # Extract category
        category = None
        for keyword, cat in CATEGORY_KEYWORDS.items():
            if keyword in query_lower:
                category = cat
                break
        
        # Extract brand
        brand = None
        for alias, brand_name in BRAND_ALIASES.items():
            if alias in query_lower:
                brand = brand_name
                break
        
        # Extract model_family based on brand
        model_family = None
        if brand:
            if brand == "Apple":
                # Find iPhone model family - just the number, not memory
                iphone_match = re.search(r'iphone\s*(\d+)', query_lower)
                if iphone_match:
                    model_family = f"iPhone {iphone_match.group(1)}"
                else:
                    model_family = "iPhone"
            elif brand == "Samsung":
                galaxy_match = re.search(r'galaxy\s*(\w+)', query_lower)
                if galaxy_match:
                    model_family = f"Galaxy {galaxy_match.group(1)}"
                else:
                    model_family = "Galaxy"
            elif brand == "Google":
                pixel_match = re.search(r'pixel\s*(\d+)', query_lower)
                if pixel_match:
                    model_family = f"Pixel {pixel_match.group(1)}"
                else:
                    model_family = "Pixel"
        
        # Extract model AFTER model_family so we can get specific model
        model = self._extract_model(query, brand)
        
        # Extract memory
        memory_gb = None
        for match in re.finditer(r'(\d+)\s*(?:gb|гб|g)', query_lower):
            memory_gb = int(match.group(1))
            break
        
        # If no memory found with regex, try text utility
        if memory_gb is None:
            memory_gb = normalize_memory(query)
        
        # Extract RAM
        ram_gb = None
        ram_match = re.search(r'(\d+)\s*(?:gb|гб|g)\s*оперативн', query_lower)
        if ram_match:
            ram_gb = int(ram_match.group(1))
        
        # Extract condition
        condition = normalize_condition(query)
        
        # Extract price range
        min_price, max_price = self._extract_price_range(query)
        
        # Extract sort order
        sort_by = extract_sort_order(query)
        
        return ProductTask(
            category=category,
            brand=brand,
            model_family=model_family,
            model=model,
            memory_gb=memory_gb,
            ram_gb=ram_gb,
            condition=condition,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
        )
    
    def _extract_model(self, query: str, brand: Optional[str]) -> Optional[str]:
        """Extract model name from query."""
        # Common model patterns - more specific
        model_patterns = [
            r'(iphone\s*1[456]\s*pro\s*max)',
            r'(iphone\s*1[456]\s*pro)',
            r'(iphone\s*1[456])',
            r'(iphone\s*se)',
            r'(galaxy\s*s\d+\s*ultra)',
            r'(galaxy\s*s\d+)',
            r'(pixel\s*\d+\s*pro)',
            r'(pixel\s*\d+)',
        ]
        
        query_lower = query.lower()
        
        for pattern in model_patterns:
            match = re.search(pattern, query_lower)
            if match:
                return match.group(1).title()
        
        # DON'T return brand as model - this is wrong!
        # If brand is found but no specific model, leave model as None
        # The validation should handle this case
        
        return None
    
    def _extract_price_range(self, query: str) -> tuple[Optional[float], Optional[float]]:
        """Extract price range from query."""
        min_price = None
        max_price = None
        
        # Match patterns like "до 50000", "до 50к"
        price_match = re.search(r'до\s*(\d+(?:[.,]\d+)?)\s*(?:руб|р\.?|к)?', query.lower())
        if price_match:
            value = price_match.group(1).replace(',', '.')
            max_price = float(value)
            if 'к' in price_match.group(0):
                max_price *= 1000
        
        # Match patterns like "от 10000"
        price_match = re.search(r'от\s*(\d+(?:[.,]\d+)?)\s*(?:руб|р\.?|к)?', query.lower())
        if price_match:
            value = price_match.group(1).replace(',', '.')
            min_price = float(value)
            if 'к' in price_match.group(0):
                min_price *= 1000
        
        return min_price, max_price
    
    def _extract_news_task(self, query: str) -> Optional[NewsTask]:
        """Extract news search parameters from query."""
        query_lower = query.lower()
        
        # Extract topic
        topic = None
        
        # Common topic patterns
        topic_patterns = [
            r'новост.*про\s+(\w+)',
            r'новости.*про\s+(\w+)',
            r'про\s+(\w+)',
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, query_lower)
            if match:
                topic = match.group(1).title()
                break
        
        # Extract time period
        period_days = extract_time_period(query)
        
        # Extract limit
        limit = 5
        limit_match = re.search(r'(\d+)\s*новост', query_lower)
        if limit_match:
            limit = int(limit_match.group(1))
        
        return NewsTask(
            topic=topic,
            period_days=period_days or 7,
            limit=limit,
        )
    
    def _calculate_confidence(
        self,
        product_task: Optional[ProductTask],
        news_task: Optional[NewsTask]
    ) -> float:
        """Calculate overall parsing confidence."""
        if not product_task and not news_task:
            return 0.0
        
        confidence = 0.5  # Base confidence
        
        if product_task:
            # More confidence if we extracted brand and specific parameters
            if product_task.brand:
                confidence += 0.15
            if product_task.memory_gb:
                confidence += 0.1
            if product_task.condition:
                confidence += 0.1
        
        if news_task:
            if news_task.topic:
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _detect_ambiguities(
        self,
        query: str,
        product_task: Optional[ProductTask],
        news_task: Optional[NewsTask]
    ) -> List[str]:
        """Detect ambiguities in the query."""
        ambiguities = []
        
        if not product_task and not news_task:
            ambiguities.append("Не удалось определить задачу из запроса")
        
        if product_task:
            if not product_task.brand:
                ambiguities.append("Бренд не указан явно")
            if not product_task.memory_gb:
                ambiguities.append("Объем памяти не указан")
            if not product_task.condition:
                ambiguities.append("Состояние товара не указано")
        
        return ambiguities
    
    def _extract_search_query(self, query: str) -> Optional[str]:
        """Extract search query from user query."""
        query_lower = query.lower()
        
        # Remove common prefixes
        prefixes = ['найди', 'найти', 'поиск', 'ищу', 'купить', 'подбери', 'зайди', 'открой', 'перейди']
        query_clean = query_lower
        for p in prefixes:
            query_clean = query_clean.replace(p, '')
        
        return query_clean.strip() if query_clean.strip() else None
    
    def _make_assumptions(
        self,
        product_task: Optional[ProductTask],
        news_task: Optional[NewsTask]
    ) -> List[str]:
        """Make assumptions based on extracted data."""
        assumptions = []
        
        if product_task:
            if not product_task.condition:
                assumptions.append("Принято condition=new, так как пользователь ищет новый товар")
        
        return assumptions


# Singleton instance
_query_parser: Optional[QueryParser] = None


def get_query_parser() -> QueryParser:
    """Get the query parser singleton."""
    global _query_parser
    if _query_parser is None:
        _query_parser = QueryParser()
    return _query_parser


def parse_user_query(query: str) -> ParsedUserQuery:
    """Parse user query into structured tasks."""
    parser = get_query_parser()
    return parser.parse(query)
