"""Execution Planner - builds dynamic execution plans from parsed queries."""

import re
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

from app.mcp.models import ExecutionPlan, ExecutionStep
from app.agents.parser import ParsedUserQuery, IntentType
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionPlanner:

    
    def __init__(self):

        self._step_counter = 0
        self._init_tool_templates()

    def _next_step_id(self) -> str:

        self._step_counter += 1
        return f"step_{self._step_counter}"

    def _app_scheme_to_web_url(self, url: str) -> str:

        app_scheme_map = {
            'app://youtube': 'https://www.youtube.com',
            'app://spotify': 'https://open.spotify.com',
            'app://netflix': 'https://www.netflix.com',
            'app://telegram': 'https://web.telegram.org',
            'app://instagram': 'https://www.instagram.com',
            'app://tiktok': 'https://www.tiktok.com',
            'app://twitter': 'https://twitter.com',
            'app://facebook': 'https://www.facebook.com',
            'app://whatsapp': 'https://web.whatsapp.com',
            'app://discord': 'https://discord.com/app',
            'app://slack': 'https://app.slack.com',
            'app://reddit': 'https://www.reddit.com',
            'app://linkedin': 'https://www.linkedin.com',
            'app://pinterest': 'https://www.pinterest.com',
            'app://zoom': 'https://zoom.us',
            'app://skype': 'https://web.skype.com',
            'app://teams': 'https://teams.microsoft.com',
            'app://dropbox': 'https://www.dropbox.com',
            'app://trello': 'https://trello.com',
            'app://asana': 'https://app.asana.com',
            'app://vk': 'https://vk.com',
            'app://viber': 'https://www.viber.com',
            'app://messenger': 'https://www.messenger.com',
        }
        

        if url.startswith('app://'):
            return app_scheme_map.get(url, url)
        
        return url

    def _extract_domain_from_url(self, url: str) -> str:

        web_url = self._app_scheme_to_web_url(url)
        match = re.search(r'https?://(?:www\.)?([a-z0-9.-]+)', web_url)
        return match.group(1).lower() if match else ""

    def _is_marketplace_domain(self, domain: str) -> bool:

        marketplace_domains = {
            'market.yandex.ru',
            'www.ozon.ru',
            'ozon.ru',
            'www.wildberries.ru',
            'wildberries.ru',
            'www.aliexpress.com',
            'aliexpress.com',
            'www.amazon.com',
            'amazon.com',
            'www.ebay.com',
            'ebay.com',
            'www.etsy.com',
            'etsy.com',
        }
        return domain in marketplace_domains

    def _plan_site_search_workflow(self, target_url: str, query_text: str) -> List[ExecutionStep]:

        web_url = self._app_scheme_to_web_url(target_url)
        domain = self._extract_domain_from_url(web_url)



        if domain in {"dzen.ru", "zen.yandex.ru"}:
            if "news" in web_url:
                stable_search_url = f"https://www.bing.com/news/search?q={quote_plus(query_text)}"
                wait_selector = "a.title, a[href*='http'], [class*='news-card']"
                result_reason = "Дождаться выдачи новостей"
            else:
                stable_search_url = f"https://www.bing.com/search?q={quote_plus(query_text + ' статьи')}"
                wait_selector = "li.b_algo h2 a, a[href*='http'], h2"
                result_reason = "Дождаться выдачи статей"

            return [
                self._make_step(
                    tool_name="browser.open_url",
                    input_data={"url": stable_search_url},
                    reasoning=f"Открыть стабильный поиск по теме: {query_text}",
                ),
                self._make_step(
                    tool_name="browser.wait_for_selector",
                    input_data={"selector": wait_selector, "timeout": 15000},
                    reasoning=result_reason,
                ),
                self._make_step(
                    tool_name="browser.get_links",
                    input_data={"limit": 5},
                    reasoning="Собрать первые 5 ссылок из выдачи",
                ),
                self._make_step(
                    tool_name="browser.get_page_text",
                    input_data={"max_length": 8000},
                    reasoning="Считать текст страницы выдачи",
                ),
            ]


        if domain in {"ru.wikipedia.org", "wikipedia.org", "www.wikipedia.org"}:
            wiki_search_url = f"https://ru.wikipedia.org/w/index.php?search={quote_plus(query_text)}&title=Служебная:Поиск&ns0=1"
            return [
                self._make_step(
                    tool_name="browser.open_url",
                    input_data={"url": wiki_search_url},
                    reasoning=f"Открыть статьи Википедии по теме: {query_text}",
                ),
                self._make_step(
                    tool_name="browser.wait_for_selector",
                    input_data={"selector": "#search, .mw-search-results li, #mw-content-text", "timeout": 15000},
                    reasoning="Дождаться результатов статей Википедии",
                ),
                self._make_step(
                    tool_name="browser.get_links",
                    input_data={"limit": 5},
                    reasoning="Собрать 5 ссылок на статьи",
                ),
                self._make_step(
                    tool_name="browser.get_page_text",
                    input_data={"max_length": 8000},
                    reasoning="Считать текст найденных материалов",
                ),
            ]


        if domain in {"apple.com", "www.apple.com"}:
            normalized_query = re.sub(r'\s+', ' ', query_text.strip())
            return [
                self._make_step(
                    tool_name="browser.open_url",
                    input_data={"url": web_url},
                    reasoning="Открыть официальный сайт Apple",
                ),
                self._make_step(
                    tool_name="browser.wait_for_selector",
                    input_data={"selector": "body", "timeout": 12000},
                    reasoning="Дождаться загрузки сайта Apple",
                ),
                self._make_step(
                    tool_name="browser.wait_for_selector",
                    input_data={"selector": "a[href], body", "timeout": 15000},
                    reasoning="Дождаться загрузки контента сайта Apple",
                ),
                self._make_step(
                    tool_name="browser.get_links",
                    input_data={"limit": 10},
                    reasoning="Собрать релевантные ссылки с сайта Apple",
                ),
                self._make_step(
                    tool_name="browser.get_page_text",
                    input_data={"max_length": 8000},
                    reasoning=f"Считать контент и цены по запросу: {normalized_query}",
                ),
            ]

        search_selectors = {
            'zen.yandex.ru': "input[placeholder*='поиск' i], input[aria-label*='поиск' i], input[type='search'], input[name='query'], input[name='text']",
            'dzen.ru': "input[placeholder*='поиск' i], input[aria-label*='поиск' i], input[type='search'], input[name='query'], input[name='text']",
            'www.youtube.com': "input#search, input[placeholder*='Search' i], input[aria-label*='Search' i]",
            'youtube.com': "input#search, input[placeholder*='Search' i], input[aria-label*='Search' i]",
            'www.google.com': "input[name='q']",
            'google.com': "input[name='q']",
        }
        search_selector = search_selectors.get(domain, "input[placeholder*='поиск' i], input[aria-label*='поиск' i], input[type='search'], input[name='query'], input[name='text'], input#search")

        return [
            self._make_step(
                tool_name="browser.open_url",
                input_data={"url": web_url},
                reasoning=f"Открыть страницу напрямую: {web_url}",
            ),
            self._make_step(
                tool_name="browser.wait_for_selector",
                input_data={"selector": search_selector, "timeout": 12000},
                reasoning="Дождаться поля поиска на странице",
            ),
            self._make_step(
                tool_name="browser.type",
                input_data={"selector": search_selector, "text": query_text},
                reasoning=f"Ввести запрос в поиск страницы: {query_text}",
            ),
            self._make_step(
                tool_name="browser.key_press",
                input_data={"key": "Enter"},
                reasoning="Запустить поиск по странице",
            ),
            self._make_step(
                tool_name="browser.wait_for_selector",
                input_data={"selector": "article, a, [role='article'], [data-testid*='search'], h2, h3", "timeout": 15000},
                reasoning="Дождаться результатов поиска внутри страницы",
            ),
            self._make_step(
                tool_name="browser.get_page_text",
                input_data={"max_length": 8000},
                reasoning="Считать результаты со страницы",
            ),
        ]

    def _make_step(
        self,
        tool_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        reasoning: str = "",
    ) -> ExecutionStep:

        return ExecutionStep(
            step_id=self._next_step_id(),
            tool_name=tool_name,
            input_data=input_data or {},
            reasoning=reasoning,
        )
    
    def _init_tool_templates(self):


        self.nav_templates = {
            "open_url": {
                "tool": "browser.open_url",
                "reasoning_template": "Открыть URL {url}",
            },
            "go_back": {
                "tool": "browser.go_back",
                "reasoning_template": "Вернуться на предыдущую страницу",
            },
            "go_forward": {
                "tool": "browser.go_forward",
                "reasoning_template": "Перейти вперёд",
            },
            "refresh": {
                "tool": "browser.refresh",
                "reasoning_template": "Обновить страницу",
            },
        }
        

        self.interaction_templates = {
            "click": {
                "tool": "browser.click",
                "reasoning_template": "Нажать на {element}",
            },
            "type_text": {
                "tool": "browser.type_text",
                "reasoning_template": "Ввести текст {text} в поле {element}",
            },
            "wait": {
                "tool": "browser.wait",
                "reasoning_template": "Ожидать {seconds} секунд",
            },
            "scroll": {
                "tool": "browser.scroll",
                "reasoning_template": "Прокрутить страницу {direction}",
            },
            "screenshot": {
                "tool": "browser.screenshot",
                "reasoning_template": "Сделать скриншот",
            },
        }
        

        self.extraction_templates = {
            "extract_page_content": {
                "tool": "browser.extract_content",
                "reasoning_template": "Извлечь контент со страницы",
            },
            "extract_links": {
                "tool": "browser.extract_links",
                "reasoning_template": "Извлечь все ссылки со страницы",
            },
            "extract_product_info": {
                "tool": "browser.extract_product_info",
                "reasoning_template": "Извлечь информацию о товаре",
            },
            "extract_news": {
                "tool": "browser.extract_news",
                "reasoning_template": "Извлечь новости со страницы",
            },
        }
        

        self.api_templates = {
            "search_products": {
                "tool": "marketplace.search_products",
                "reasoning_template": "Искать товары: {query}",
            },
            "get_product_details": {
                "tool": "marketplace.get_product_details",
                "reasoning_template": "Получить детали товара {product_id}",
            },
            "search_news": {
                "tool": "news.search_news",
                "reasoning_template": "Искать новости: {topic}",
            },
            "get_news_articles": {
                "tool": "news.get_articles",
                "reasoning_template": "Получить статьи по теме {topic}",
            },
        }
        

        self.intent_reasoning = {
            IntentType.BROWSER_NAVIGATION: "Требуется навигация в браузере",
            IntentType.BROWSER_INTERACTION: "Требуется взаимодействие со страницей",
            IntentType.INFO_RETRIEVAL: "Требуется извлечение информации",
            IntentType.PRODUCT_SEARCH: "Требуется поиск товаров",
            IntentType.NEWS_SEARCH: "Требуется поиск новостей",
            IntentType.MULTI_STEP: "Требуется многошаговый план",
            IntentType.MIXED_TASK: "Смешанная задача",
        }
    
    def create_plan(self, parsed_query: ParsedUserQuery) -> ExecutionPlan:

        self._step_counter = 0
        steps: List[ExecutionStep] = []
        reasoning_lines: List[str] = []
        

        intent = parsed_query.intent_type
        reasoning_lines.append(self.intent_reasoning.get(intent, "Определён неизвестный интент"))
        

        hints = parsed_query.execution_hints
        
        if hints.requires_browser:
            steps.extend(self._plan_browser_actions(parsed_query))
        
        if hints.requires_extraction:
            steps.extend(self._plan_extraction(parsed_query))
        
        if hints.requires_domain_workflow:
            steps.extend(self._plan_domain_workflow(parsed_query))
        
        if parsed_query.news_topic:
            steps.extend(self._plan_news_search(parsed_query))
        
        if parsed_query.brand or parsed_query.model:
            steps.extend(self._plan_product_search(parsed_query))
        
        if not steps:
            # Fallback: universal web-research flow for arbitrary queries
            if parsed_query.url:
                web_url = self._app_scheme_to_web_url(parsed_query.url)
                steps.append(
                    self._make_step(
                        tool_name="browser.open_url",
                        input_data={"url": web_url},
                        reasoning="Открыть указанный URL",
                    ),
                )
                steps.append(
                    self._make_step(
                        tool_name="browser.get_page_text",
                        input_data={"max_length": 12000},
                        reasoning="Считать текст с открытой страницы",
                    ),
                )
                steps.append(
                    self._make_step(
                        tool_name="browser.get_links",
                        input_data={"limit": 30},
                        reasoning="Собрать ссылки со страницы",
                    ),
                )
            else:
                search_query = (
                    parsed_query.execution_hints.search_query
                    or parsed_query.news_topic
                    or parsed_query.raw_query
                )
                search_url = f"https://www.google.com/search?q={quote_plus(search_query)}"
                steps.extend(self._plan_generic_research(search_url, search_query))
        
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            steps=steps,
            reasoning="\n".join(reasoning_lines),
            query=parsed_query.raw_query,
        )

    def _plan_generic_research(self, search_url: str, query_text: str) -> List[ExecutionStep]:

        return [
            self._make_step(
                tool_name="browser.open_url",
                input_data={"url": search_url},
                reasoning=f"Открыть поисковую выдачу по запросу: {query_text}",
            ),
            self._make_step(
                tool_name="browser.wait_for_selector",
                input_data={"selector": "a[href], h3", "timeout": 12000},
                reasoning="Дождаться загрузки результатов Google поиска",
            ),
            self._make_step(
                tool_name="browser.click",
                input_data={"selector": "a[href*='http']:first-of-type"},
                reasoning="Кликнуть на первый релевантный результат",
            ),
            self._make_step(
                tool_name="browser.wait_for_selector",
                input_data={"selector": "body", "timeout": 12000},
                reasoning="Дождаться загрузки целевой страницы",
            ),
            self._make_step(
                tool_name="browser.get_page_text",
                input_data={"max_length": 5000},
                reasoning="Получить информацию со страницы",
            ),
        ]
    
    def _plan_browser_actions(self, parsed_query: ParsedUserQuery) -> List[ExecutionStep]:

        steps = []
        hints = parsed_query.execution_hints
        
        # Handle URL opening
        target_url = hints.target_url or parsed_query.url
        if target_url and not (hints.search_query and hints.requires_multi_step_plan):
            # Convert app:// schemes to web URLs for Playwright
            web_url = self._app_scheme_to_web_url(target_url)
            
            steps.append(
                self._make_step(
                    tool_name="browser.open_url",
                    input_data={"url": web_url},
                    reasoning=f"Открыть URL: {web_url}",
                ),
            )
        

        if hints.search_query and hints.requires_multi_step_plan:
            if target_url:
                domain = self._extract_domain_from_url(target_url)
                if not self._is_marketplace_domain(domain):
                    steps.extend(self._plan_site_search_workflow(target_url, hints.search_query))
                else:
                    # Keep marketplace flows unchanged.
                    pass
            else:
                steps.append(
                    self._make_step(
                        tool_name="browser.type",
                        input_data={
                            "selector": "input[name='q'], input[type='search'], input[placeholder*='search' i], input[placeholder*='поиск' i]",
                            "text": hints.search_query,
                        },
                        reasoning=f"Ввести поисковый запрос в поле поиска: {hints.search_query}",
                    ),
                )
                steps.append(
                    self._make_step(
                        tool_name="browser.key_press",
                        input_data={"key": "Enter"},
                        reasoning="Нажать Enter для поиска",
                    ),
                )
                steps.append(
                    self._make_step(
                        tool_name="browser.get_links",
                        input_data={"limit": 20},
                        reasoning="Собрать ссылки из результатов поиска",
                    ),
                )
        

        if hints.button_text:
            steps.append(
                self._make_step(
                    tool_name="browser.click",
                    input_data={"selector": hints.button_text},
                    reasoning=f"Нажать на кнопку: {hints.button_text}",
                ),
            )
        

        if hints.input_text:
            steps.append(
                self._make_step(
                    tool_name="browser.type",
                    input_data={"selector": "input, textarea", "text": hints.input_text},
                    reasoning=f"Ввести текст: {hints.input_text}",
                ),
            )
        
        return steps
    
    def _plan_extraction(self, parsed_query: ParsedUserQuery) -> List[ExecutionStep]:

        steps = []
        

        if parsed_query.intent_type == IntentType.PRODUCT_SEARCH:
            steps.append(
                self._make_step(
                    tool_name="browser.get_page_text",
                    input_data={"max_length": 10000},
                    reasoning="Извлечь текст страницы с товарами",
                ),
            )
        elif parsed_query.intent_type == IntentType.NEWS_SEARCH:
            steps.append(
                self._make_step(
                    tool_name="browser.get_page_text",
                    input_data={"max_length": 10000},
                    reasoning="Извлечь текст страницы с новостями",
                ),
            )
        else:
            steps.append(
                self._make_step(
                    tool_name="browser.get_page_text",
                    input_data={"max_length": 10000},
                    reasoning="Извлечь контент страницы",
                ),
            )
        
        return steps
    
    def _plan_domain_workflow(self, parsed_query: ParsedUserQuery) -> List[ExecutionStep]:

        steps = []
        

        if parsed_query.brand or parsed_query.model or parsed_query.execution_hints.search_query:
            query_parts = []
            if parsed_query.execution_hints.search_query:
                query_parts.append(parsed_query.execution_hints.search_query)
            elif parsed_query.brand or parsed_query.model:
                if parsed_query.brand:
                    query_parts.append(parsed_query.brand)
                if parsed_query.model:
                    query_parts.append(parsed_query.model)
                if parsed_query.memory_gb:
                    query_parts.append(f"{parsed_query.memory_gb}GB")
            
            search_query = " ".join(query_parts)
            if search_query:
                market_url = f"https://market.yandex.ru/search?text={quote_plus(search_query)}"
                steps.append(
                    self._make_step(
                        tool_name="browser.open_url",
                        input_data={"url": market_url},
                        reasoning=f"Открыть поиск товаров: {search_query}",
                    ),
                )
                steps.append(
                    self._make_step(
                        tool_name="browser.wait_for_selector",
                        input_data={"selector": "a[href*='/product--'], article, [data-autotest-id='product-snippet']", "timeout": 12000},
                        reasoning="Дождаться загрузки результатов маркетплейса",
                    ),
                )
                steps.append(
                    self._make_step(
                        tool_name="browser.get_page_text",
                        input_data={"max_length": 10000},
                        reasoning="Считать результаты поиска товаров",
                    ),
                )
        
        return steps
    
    def _plan_news_search(self, parsed_query: ParsedUserQuery) -> List[ExecutionStep]:
        """Plan news search actions."""
        return []
    
    def _plan_product_search(self, parsed_query: ParsedUserQuery) -> List[ExecutionStep]:
        """Plan product search actions."""
        return []



_planner: Optional[ExecutionPlanner] = None


def get_planner() -> ExecutionPlanner:

    global _planner
    if _planner is None:
        _planner = ExecutionPlanner()
    return _planner



Planner = ExecutionPlanner
