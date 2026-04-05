"""Query Parser - NLP parsing for extracting intent and entities."""

import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Intent types for user queries."""
    BROWSER_NAVIGATION = "browser_navigation"
    BROWSER_INTERACTION = "browser_interaction"
    INFO_RETRIEVAL = "information_retrieval"
    PRODUCT_SEARCH = "product_search"
    NEWS_SEARCH = "news_search"
    MULTI_STEP = "multi_step"
    MIXED_TASK = "mixed_task"
    UNKNOWN = "unknown"


@dataclass
class ExecutionHints:
    requires_browser: bool = False
    requires_extraction: bool = False
    requires_multi_step_plan: bool = False
    requires_domain_workflow: bool = False
    target_url: Optional[str] = None
    button_text: Optional[str] = None
    input_text: Optional[str] = None
    search_query: Optional[str] = None
    page_action: Optional[str] = None


@dataclass
class ParsedUserQuery:
    raw_query: str
    normalized_query: str
    intent_type: IntentType
    execution_hints: ExecutionHints
    
    # Product search entities
    brand: Optional[str] = None
    model: Optional[str] = None
    memory_gb: Optional[int] = None
    condition: Optional[str] = None
    
    # News search entities
    news_topic: Optional[str] = None
    period_days: Optional[int] = None
    
    # General
    url: Optional[str] = None
    confidence: float = 0.5


class QueryParser:

    
    def __init__(self):

        self._init_patterns()
    
    def _init_patterns(self):


        self.nav_patterns = [
            r'зайди\s+на\s+(.+)$',
            r'зайди\s+в\s+(?:приложение\s+)?(.+)$',
            r'открой\s+(?:(?:сайт|страницу|приложение)\s+)?(.+)$',
            r'перейди\s+(?:(?:на|в)\s+)?(.+)$',
            r'посети\s+(?:(?:сайт|приложение)\s+)?(.+)$',
            r'go\s+(?:to\s+)?(.+)$',
            r'open\s+(?:(?:site|app|application)\s+)?(.+)$',
        ]

        self.url_mappings = {

            'яндекс': 'https://yandex.ru',
            'yandex': 'https://yandex.ru',
            'яндекс маркет': 'https://market.yandex.ru',
            'маркет': 'https://market.yandex.ru',
            'яндекс карты': 'https://maps.yandex.ru',
            'карты': 'https://maps.yandex.ru',
            'mail': 'https://mail.ru',
            'mail.ru': 'https://mail.ru',
            'mailru': 'https://mail.ru',
            'яндекс почта': 'https://mail.yandex.ru',
            'яндекс диск': 'https://disk.yandex.ru',
            'авито': 'https://www.avito.ru',
            'avito': 'https://www.avito.ru',
            '2gis': 'https://2gis.ru',
            'двугис': 'https://2gis.ru',
            'дзен': 'https://zen.yandex.ru',
            'яндекс дзен': 'https://zen.yandex.ru',
            'zen': 'https://zen.yandex.ru',
            
            'ozon': 'https://www.ozon.ru',
            'озон': 'https://www.ozon.ru',
            'wildberries': 'https://www.wildberries.ru',
            'вб': 'https://www.wildberries.ru',
            'wildberries.ru': 'https://www.wildberries.ru',
            'aliexpress': 'https://www.aliexpress.com',
            'алиэкспресс': 'https://www.aliexpress.com',
            'amazon': 'https://www.amazon.com',
            'амазон': 'https://www.amazon.com',
            'ebay': 'https://www.ebay.com',
            'etsy': 'https://www.etsy.com',
            

            'вк': 'app://vk',
            'vk': 'app://vk',
            'vkontakte': 'app://vk',
            'вконтакте': 'app://vk',
            'telegram': 'app://telegram',
            'телеграм': 'app://telegram',
            'tg': 'app://telegram',
            'instagram': 'app://instagram',
            'инстаграм': 'app://instagram',
            'insta': 'app://instagram',
            'tiktok': 'app://tiktok',
            'тикток': 'app://tiktok',
            'facebook': 'app://facebook',
            'фейсбук': 'app://facebook',
            'messenger': 'app://messenger',
            'viber': 'app://viber',
            'вайбер': 'app://viber',
            'whatsapp': 'app://whatsapp',
            'вацап': 'app://whatsapp',
            'wechat': 'app://wechat',
            'qq': 'app://qq',
            'twitter': 'app://twitter',
            'x': 'app://twitter',
            'твиттер': 'app://twitter',
            
            'youtube': 'app://youtube',
            'ютуб': 'app://youtube',
            'youtube.com': 'app://youtube',
            'youtu': 'app://youtube',
            'netflix': 'app://netflix',
            'нетфликс': 'app://netflix',
            'spotify': 'app://spotify',
            'спотифай': 'app://spotify',
            'soundcloud': 'app://soundcloud',
            'яндекс музыка': 'https://music.yandex.ru',
            'музыка': 'https://music.yandex.ru',
            'twitch': 'app://twitch',
            'твич': 'app://twitch',
            'rumble': 'https://rumble.com',
            
            'github': 'https://github.com',
            'гитхаб': 'https://github.com',
            'stackoverflow': 'https://stackoverflow.com',
            'stack overflow': 'https://stackoverflow.com',
            'so': 'https://stackoverflow.com',
            'reddit': 'app://reddit',
            'реддит': 'app://reddit',
            'discord': 'app://discord',
            'дискорд': 'app://discord',
            'figma': 'https://www.figma.com',
            'фигма': 'https://www.figma.com',
            'gitlab': 'https://gitlab.com',
            'gitea': 'https://gitea.io',
            'mdn': 'https://developer.mozilla.org',
            'w3schools': 'https://www.w3schools.com',
            'w3': 'https://www.w3schools.com',
            'codepen': 'https://codepen.io',
            'jsfiddle': 'https://jsfiddle.net',
            'repl.it': 'https://replit.com',
            'replit': 'https://replit.com',
            'glitch': 'https://glitch.com',
            'stackblitz': 'https://stackblitz.com',
            'codeandbox': 'https://codesandbox.io',
            'ideone': 'https://ideone.com',
            'habr': 'https://habr.com',
            'habrahabr': 'https://habr.com',
            'хабр': 'https://habr.com',
            
            'coursera': 'https://www.coursera.org',
            'курсера': 'https://www.coursera.org',
            'udemy': 'https://www.udemy.com',
            'udacity': 'https://www.udacity.com',
            'codecademy': 'https://www.codecademy.com',
            'freecodecamp': 'https://www.freecodecamp.org',
            'khan academy': 'https://www.khanacademy.org',
            'skillshare': 'https://www.skillshare.com',
            'medium': 'https://medium.com',
            'медиум': 'https://medium.com',
            'dev.to': 'https://dev.to',
            'css-tricks': 'https://css-tricks.com',
            'smashing magazine': 'https://www.smashingmagazine.com',
            'json.org': 'https://www.json.org',
            'regex101': 'https://regex101.com',
            'regex': 'https://regex101.com',
            
            'wikipedia': 'https://wikipedia.org',
            'википедия': 'https://ru.wikipedia.org',
            'википедию': 'https://ru.wikipedia.org',
            'википедии': 'https://ru.wikipedia.org',
            'википедией': 'https://ru.wikipedia.org',
            'вики': 'https://ru.wikipedia.org',
            'google': 'https://google.com',
            'гугл': 'https://google.com',
            'bing': 'https://www.bing.com',
            'duckduckgo': 'https://duckduckgo.com',
            'duck': 'https://duckduckgo.com',
            'amazon s3': 'https://aws.amazon.com/s3',
            'aws': 'https://aws.amazon.com',
            'digitalocean': 'https://www.digitalocean.com',
            'heroku': 'https://www.heroku.com',
            'vercel': 'https://vercel.com',
            'netlify': 'https://www.netlify.com',
            'firebase': 'https://firebase.google.com',
            'mongodb': 'https://www.mongodb.com',
            'postgresql': 'https://www.postgresql.org',
            'mysql': 'https://www.mysql.com',
            'oracle': 'https://www.oracle.com',
            'docker': 'https://www.docker.com',
            'kubernetes': 'https://kubernetes.io',
            'kubernetes.io': 'https://kubernetes.io',
            
            'notion': 'https://www.notion.so',
            'нотион': 'https://www.notion.so',
            'trello': 'app://trello',
            'трелло': 'app://trello',
            'asana': 'app://asana',
            'monday': 'https://monday.com',
            'slack': 'app://slack',
            'слак': 'app://slack',
            'teams': 'app://teams',
            'zoom': 'app://zoom',
            'зум': 'app://zoom',
            'skype': 'app://skype',
            'скайп': 'app://skype',
            'drive': 'https://drive.google.com',
            'google drive': 'https://drive.google.com',
            'onedrive': 'https://onedrive.live.com',
            'dropbox': 'app://dropbox',
            'icloud': 'https://www.icloud.com',
            
            'linkedin': 'app://linkedin',
            'линкедин': 'app://linkedin',
            'crunchbase': 'https://www.crunchbase.com',
            'producthunt': 'https://www.producthunt.com',
            'angel': 'https://angel.co',
            
            'pinterest': 'app://pinterest',
            'пинтерест': 'app://pinterest',
            'flickr': 'https://www.flickr.com',
            'imgur': 'https://imgur.com',
            'pastebin': 'https://pastebin.com',
            'gist': 'https://gist.github.com',
            'vpn': 'https://www.vpngate.net',
            'torrent': 'https://thepiratebay.org',
        }
        
        self.interaction_patterns = [
            r'нажми\s+(?:на\s+)?([^\s]+)',
            r'кликни\s+(?:на\s+)?([^\s]+)',
            r'введи\s+(.+?)(?:\s+в|\s+на)',
            r'напечатай\s+(.+)',
        ]
        
        self.brand_aliases = {
            'apple': 'Apple', 'iphone': 'Apple',
            'samsung': 'Samsung', 'galaxy': 'Samsung',
            'google': 'Google', 'pixel': 'Google',
            'xiaomi': 'Xiaomi', 'redmi': 'Xiaomi',
            'huawei': 'Huawei', 'honor': 'Honor',
            'oneplus': 'OnePlus', 'oppo': 'OPPO',
            'vivo': 'Vivo', 'realme': 'Realme',
        }
        
        self.product_keywords = ['найди', 'найти', 'поиск', 'ищу', 'купить', 'подбери', 'цена', 'товар', 'iphone', 'samsung', 'xiaomi']
        
        self.news_keywords = ['новост', 'новости', 'news', 'собери']

        self.article_keywords = ['стат', 'статьи', 'статья', 'пост', 'публикац', 'обзор', 'обзоры']
        
        self.browser_keywords = ['сайт', 'страницу', 'открой', 'зайди', 'перейди', 'верни', 'заголовок', 'текст']
    
    def parse(self, query: str) -> ParsedUserQuery:

        query_lower = query.lower().strip()
        

        intent_type, hints = self._detect_intent(query_lower)
        

        brand, model, memory = self._extract_product_entities(query_lower)
        

        topic = None
        if intent_type in [IntentType.NEWS_SEARCH, IntentType.MULTI_STEP]:
            topic = self._extract_news_topic(query_lower)
        

        url = None
        if intent_type == IntentType.BROWSER_NAVIGATION:
            url = self._extract_url(query_lower)
        

        if not hints.search_query or hints.requires_multi_step_plan:
            search_query = self._extract_search_query(query_lower)

            if search_query and not hints.search_query:

                explicit_patterns = [
                    r'найди\s+(.+)$',
                    r'собери\s+(.+)$',
                    r'покажи\s+(.+)$',
                    r'расскажи\s+про\s+(.+)$',
                    r'search\s+for\s+(.+)$',
                    r'find\s+(.+)$',
                ]
                if any(re.search(p, query_lower) for p in explicit_patterns):
                    hints.search_query = search_query
                elif intent_type != IntentType.BROWSER_NAVIGATION:
                    hints.search_query = search_query
        
        confidence = self._calculate_confidence(intent_type, brand, model, memory, topic)
        
        return ParsedUserQuery(
            raw_query=query,
            normalized_query=query.strip(),
            intent_type=intent_type,
            execution_hints=hints,
            brand=brand,
            model=model,
            memory_gb=memory,
            news_topic=topic,
            url=url,
            confidence=confidence,
        )
    
    def _detect_intent(self, query: str) -> tuple[IntentType, ExecutionHints]:
        hints = ExecutionHints()


        for pattern in self.nav_patterns:
            match = re.search(pattern, query)
            if not match:
                continue

            raw_destination = match.group(1).strip()
            action_match = re.split(r'\s+(?:и|ищи|поищи|найди|покажи|открой)\s+', raw_destination, 1)

            if len(action_match) > 1:
                app_name = action_match[0].strip()
                action_part = self._cleanup_search_phrase(action_match[1].strip())

                hints.requires_browser = True
                hints.target_url = self._normalize_destination_to_url(app_name)
                if action_part:
                    hints.search_query = action_part
                    hints.requires_multi_step_plan = True
                return IntentType.BROWSER_NAVIGATION, hints

            hints.requires_browser = True
            hints.target_url = self._normalize_destination_to_url(raw_destination)

            alias = self._find_destination_alias(raw_destination)
            if alias:
                tail = raw_destination[len(alias):].strip()
                tail = self._cleanup_search_phrase(tail)
                if tail:
                    hints.search_query = tail
                    hints.requires_multi_step_plan = True

            return IntentType.BROWSER_NAVIGATION, hints


        for pattern in self.interaction_patterns:
            if re.search(pattern, query):
                return IntentType.BROWSER_INTERACTION, hints


        info_keywords = ['верни', 'получи', 'извлеки', 'дай', 'покажи', 'заголовок', 'текст', 'контент']
        if any(kw in query for kw in info_keywords):
            hints.requires_extraction = True
            return IntentType.INFO_RETRIEVAL, hints


        has_articles = any(kw in query for kw in self.article_keywords)
        if has_articles:
            article_topic = self._extract_article_topic(query)
            if not article_topic:
                fallback_topic = self._extract_search_query(query)
                article_topic = self._cleanup_search_phrase(fallback_topic) if fallback_topic else None
            return IntentType.BROWSER_NAVIGATION, ExecutionHints(
                requires_browser=True,
                requires_multi_step_plan=bool(article_topic),
                target_url='https://ru.wikipedia.org',
                search_query=article_topic,
            )


        has_product = any(kw in query for kw in self.product_keywords)
        has_news = any(kw in query for kw in self.news_keywords)
        has_browser = any(kw in query for kw in self.browser_keywords)

        search_query = self._extract_search_query(query)
        hints.search_query = search_query


        if has_news:
            news_topic = self._extract_news_topic(query) or search_query
            return IntentType.NEWS_SEARCH, ExecutionHints(
                requires_browser=True,
                requires_multi_step_plan=bool(news_topic),
                target_url='https://dzen.ru/news',
                search_query=news_topic,
            )


        if 'википед' in query or 'wikipedia' in query:
            wiki_topic = self._extract_search_query(query) or query
            wiki_topic = self._cleanup_search_phrase(wiki_topic) if wiki_topic else None
            return IntentType.BROWSER_NAVIGATION, ExecutionHints(
                requires_browser=True,
                requires_multi_step_plan=bool(wiki_topic),
                target_url='https://ru.wikipedia.org',
                search_query=wiki_topic,
            )

        if has_product:
            if has_browser:
                return IntentType.BROWSER_NAVIGATION, ExecutionHints(
                    requires_browser=True,
                    requires_domain_workflow=True,
                    search_query=search_query,
                )
            return IntentType.PRODUCT_SEARCH, ExecutionHints(
                requires_domain_workflow=True,
                search_query=search_query,
            )

        if has_browser:
            return IntentType.BROWSER_NAVIGATION, hints

        return IntentType.UNKNOWN, hints

    def _find_destination_alias(self, destination: str) -> Optional[str]:
        """Find a known site/app alias inside a destination string."""
        lowered = destination.lower().strip()
        aliases = sorted(self.url_mappings.keys(), key=len, reverse=True)

        for alias in aliases:
            if lowered.startswith(alias):
                return alias

        for alias in aliases:
            if alias in lowered:
                return alias

        return None

    def _cleanup_search_phrase(self, phrase: str) -> str:

        cleaned = phrase.strip()
        cleaned = re.sub(r'^[\s,.:;!?\-]+', '', cleaned)
        cleaned = re.sub(
            r'^(?:и\s+)?(?:найди|ищи|поищи|покажи|посмотри|открой|запусти|статьи?|новости?|видео|музыку|песни?|трек(?:и|ов)?|публикации|посты)\s+',
            '',
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r'^\d+\s+стат\w*\s+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^стат\w*\s+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^(?:о|про)\s+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def _extract_product_entities(self, query: str) -> tuple[Optional[str], Optional[str], Optional[int]]:

        brand = None
        model = None
        memory = None


        for alias, full_brand in self.brand_aliases.items():
            if alias in query:
                brand = full_brand
                break


        model_patterns = [
            r'(iphone\s+\d+\s*\w*)',
            r'(galaxy\s+\w+\s*\d*)',
            r'(pixel\s+\d+)',
            r'(\w+\s+\d+gb)',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                model = match.group(1)
                break


        memory_pattern = r'(\d+)\s*gb'
        match = re.search(memory_pattern, query, re.IGNORECASE)
        if match:
            memory = int(match.group(1))

        return brand, model, memory

    def _extract_news_topic(self, query: str) -> Optional[str]:
        """Extract news topic from query."""
        patterns = [
            r'новост(?:и|ей)\s+(?:о|про)?\s*(.+)',
            r'собери\s+новост(?:и|ей)\s+(?:о|про)?\s*(.+)',
            r'найди\s+новост(?:и|ей)\s+(?:о|про)?\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                topic = self._cleanup_search_phrase(match.group(1))
                if topic and len(topic) > 1:
                    return topic

        return None

    def _extract_article_topic(self, query: str) -> Optional[str]:

        patterns = [
            r'найди\s+\d+\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'найди\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'собери\s+\d+\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'собери\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'покажи\s+\d+\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'покажи\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'\d+\s+стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'стат(?:ья|ьи|ей|ью)?\s+(?:о|про)?\s*(.+)',
            r'обзор(?:ы)?\s+(?:о|про)?\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                topic = self._cleanup_search_phrase(match.group(1))
                if topic and len(topic) > 1:
                    return topic

        return None

    def _extract_search_query(self, query: str) -> Optional[str]:
        patterns = [
            r'найди\s+(.+)$',
            r'собери\s+(.+)$',
            r'покажи\s+(.+)$',
            r'расскажи\s+про\s+(.+)$',
            r'что\s+знаешь\s+про\s+(.+)$',
            r'search\s+for\s+(.+)$',
            r'find\s+(.+)$',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if not match:
                continue

            search_term = match.group(1)
            search_term = search_term.rstrip('.,!?;:-')
            if search_term and len(search_term) > 1:
                return search_term

        cleaned_query = query.strip().rstrip('.,!?;:-')
        if len(cleaned_query) > 2:
            return cleaned_query
        return None

    def _extract_url(self, query: str) -> Optional[str]:

        for pattern in self.nav_patterns:
            match = re.search(pattern, query)
            if match:
                return self._normalize_destination_to_url(match.group(1))

        return None

    def _normalize_destination_to_url(self, destination: str) -> str:

        cleaned = destination.strip().strip('"\'')
        cleaned = re.sub(
            r'^(?:сайт|сайта|чайт|страницу|страница|приложение|site|app|application)\s+',
            '',
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r'\b(пожалуйста|плиз|please)\b', '', cleaned, flags=re.IGNORECASE).strip()


        tokens = re.split(r'\s+', cleaned)
        for token in tokens:
            token = token.strip('.,!?;:()[]{}"\'')
            if token.startswith(('http://', 'https://')):
                return token
            if '.' in token and re.fullmatch(r'[a-zA-Z0-9.-]+', token):
                return f'https://{token}' if not token.startswith('www.') else f'https://{token}'

        if '://' in cleaned or ('.' in cleaned and len(cleaned.split('.')[-1]) <= 4):
            cleaned = re.sub(r'[,!?;)\s]+$', '', cleaned)
        else:
            cleaned = cleaned.rstrip('.,!?;:)')

        lowered = cleaned.lower()

        if 'википед' in lowered:
            return 'https://ru.wikipedia.org'
        if re.search(r'\bwikipedia\b|\bwiki\b', lowered):
            return 'https://wikipedia.org'


        if cleaned.startswith(('http://', 'https://')):
            return cleaned

        if lowered in self.url_mappings:
            return self.url_mappings[lowered]

        for name, full_url in self.url_mappings.items():
            if name in lowered:
                return full_url

        if '.' in cleaned:
            if cleaned.startswith('www.'):
                return f'https://{cleaned}'
            return f'https://{cleaned}'

        slug = lowered.replace(' ', '')
        if re.fullmatch(r'[a-z0-9_-]+', slug):
            return f'https://{slug}.com'

        return f'https://www.google.com/search?q={cleaned}'

    def _calculate_confidence(
        self,
        intent: IntentType,
        brand: Optional[str],
        model: Optional[str],
        memory: Optional[int],
        topic: Optional[str],
    ) -> float:
        confidence = 0.5

        if intent in [IntentType.PRODUCT_SEARCH, IntentType.MULTI_STEP]:
            if brand:
                confidence += 0.2
            if model:
                confidence += 0.15
            if memory:
                confidence += 0.15

        if intent in [IntentType.NEWS_SEARCH, IntentType.MULTI_STEP]:
            if topic:
                confidence += 0.3

        if intent == IntentType.BROWSER_NAVIGATION:
            confidence += 0.3

        return min(confidence, 1.0)



_parser: Optional[QueryParser] = None


def get_query_parser() -> QueryParser:

    global _parser
    if _parser is None:
        _parser = QueryParser()
    return _parser
