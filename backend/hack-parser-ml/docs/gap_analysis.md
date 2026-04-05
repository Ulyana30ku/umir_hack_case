# GAP ANALYSIS: Текущее vs Требуемое

## Что есть сейчас (текущее состояние):

### ✅ Сильные части (сохранить):
1. **Agent/Orchestrator** ([`app/agents/orchestrator.py`](app/agents/orchestrator.py)) - базовая координация шагов
2. **Query Parser** ([`app/services/query_parser.py`](app/services/query_parser.py)) - парсинг запроса, извлечение сущностей
3. **Planner** ([`app/agents/planner.py`](app/agents/planner.py)) - создание плана выполнения
4. **Services** - validation, ranking, answer composing
5. **Trace** - логирование шагов с объяснениями
6. **API layer** - FastAPI endpoints

### ❌ Проблемы (нужно исправить):

1. **Нет Browser Automation**
   - Нет Playwright integration
   - Нет реального управления браузером
   - Все действия "в памяти", не в реальном браузере

2. **Нет Tool Registry**
   - Инструменты разбросаны по коду
   - Нет единого интерфейса
   - Агент вызывает функции напрямую, а не через registry

3. **Query Parser заточен только под товары/новости**
   - Не понимает "зайди", "нажми", "введи", "открой"
   - Нет intent classification для browser tasks

4. **Продуктовый/новостной pipelines работают на моках**
   - Товары генерируются в коде
   - Нет реального парсинга с маркетплейсов

5. **Нет real browser actions**
   - Нельзя кликнуть, скроллить, ввести текст
   - Нельзя извлечь данные со страницы

6. **Trace неполный**
   - Нет screenshot_path
   - Нет browser_url на каждом шаге

---

## Новая архитектура Browser Agent System:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                  │
│         "зайди на ozon, найди iPhone 15 и верни цену"              │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      QUERY UNDERSTANDING                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │ Intent          │  │ Entities       │  │ Execution Hints     │  │
│  │ Classification  │  │ Extraction     │  │                     │  │
│  │                 │  │                 │  │ requires_browser   │  │
│  │ - navigation    │  │ - url          │  │ requires_extraction│  │
│  │ - interaction   │  │ - search_query │  │ multi_step         │  │
│  │ - info_retrieval│  │ - button_text  │  │                    │  │
│  │ - product_search│  │ - constraints  │  │                    │  │
│  │ - news_search   │  │                 │  │                    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           PLANNER                                   │
│                                                                     │
│   На основе intent_type -> создает ExecutionPlan                   │
│   План = последовательность tool calls                              │
│                                                                     │
│   browser_navigation:                                              │
│     1. browser_open_url(url)                                       │
│                                                                     │
│   browser_interaction:                                             │
│     1. browser_open_url(url)                                       │
│     2. browser_type(search_field, query)                           │
│     3. browser_press(Enter)                                        │
│                                                                     │
│   product_search:                                                   │
│     1. browser_open_url(ozon)                                      │
│     2. browser_type(search, query)                                │
│     3. browser_press(Enter)                                       │
│     4. browser_wait_for_results()                                 │
│     5. open_first_product()                                        │
│     6. extract_product_fields()                                    │
│     7. validate_product()                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        TOOL REGISTRY                                │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                      BROWSER TOOLS                          │   │
│   ├─────────────────────────────────────────────────────────────┤   │
│   │ browser_open_url(url)           → {url, status}            │   │
│   │ browser_click(selector)        → {success, element}       │   │
│   │ browser_type(selector, text)   → {success}                │   │
│   │ browser_scroll(direction)      → {new_position}          │   │
│   │ browser_wait_for_text(text)    → {found}                  │   │
│   │ browser_get_page_text()         → {text}                   │   │
│   │ browser_get_page_html()         → {html}                   │   │
│   │ browser_get_links()             → [{url, text}]           │   │
│   │ browser_screenshot()            → {path}                  │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    DATA TOOLS                               │   │
│   ├─────────────────────────────────────────────────────────────┤   │
│   │ extract_product_fields()      → {product}                 │   │
│   │ extract_news_items()           → [{news}]                  │   │
│   │ search_products(query)         → [{products}]              │   │
│   │ search_news(topic)             → [{news}]                  │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BROWSER AUTOMATION LAYER                        │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              BrowserSessionManager                          │   │
│   │  - create_session()                                         │   │
│   │  - close_session()                                          │   │
│   │  - get_session(id)                                          │   │
│   │                                                              │   │
│   │  Playwright integration:                                    │   │
│   │  - headless/headful mode                                    │   │
│   │  - viewport configuration                                   │   │
│   │  - network interception                                    │   │
│   │  - error handling                                           │   │
│   └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EXECUTION + TRACE                             │
│                                                                     │
│   for each step in plan:                                           │
│     - execute tool                                                  │
│     - log step (start, end, input, output, error)                  │
│     - save screenshot if error                                     │
│     - continue or abort                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FINAL RESPONSE                             │
│   {                                                                │
│     "run_id": "...",                                               │
│     "status": "success|partial|failed",                            │
│     "result": {                                                    │
│       "summary": "...",                                            │
│       "browser_result": {                                         │
│         "final_url": "...",                                        │
│         "actions_completed": [...],                               │
│         "page_text_excerpt": "..."                                │
│       },                                                           │
│       "product": {...} | null,                                    │
│       "news": [...] | null,                                      │
│       "trace": {...}                                              │
│     }                                                              │
│   }                                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Файлы для создания/изменения:

### Новые файлы:

1. **`app/tools/browser/base.py`** - BaseBrowserTool абстрактный класс
2. **`app/tools/browser/session.py`** - BrowserSessionManager (Playwright)
3. **`app/tools/browser/tools.py`** - Все browser tools
4. **`app/tools/registry.py`** - ToolRegistry
5. **`app/tools/browser/__init__.py`** - Package init
6. **`app/schemas/task.py`** - Task, Step schemas

### Изменяемые файлы:

1. **`app/services/query_parser.py`** - Добавить intent classification
2. **`app/agents/planner.py`** - Добавить browser planning
3. **`app/agents/orchestrator.py`** - Интегрировать tool registry + browser
4. **`app/api/routes/agent.py`** - Обновить response format
5. **`app/schemas/query.py`** - Добавить intent_type, execution_hints
6. **`app/schemas/trace.py`** - Расширить trace schema

### Product/News как частные сценарии:

- [`app/integrations/marketplaces/yandex_market.py`](app/integrations/marketplaces/yandex_market.py) - оставить, использовать для fallback
- [`app/integrations/news/rss_news.py`](app/integrations/news/rss_news.py) - оставить, это real data
- Создать browser-based product workflow: browser → search → click → extract → validate
- Создать browser-based news workflow: browser → navigate → extract → rank

---

## Priority реализации:

1. **BrowserSessionManager** (Playwright) - основа
2. **ToolRegistry** - интерфейс для всех tools
3. **Browser Tools** (open, click, type, scroll, get_text)
4. **Query Parser** (intent classification)
5. **Planner** (browser plans)
6. **Orchestrator** (интеграция)
7. **API** (response format)
8. **Tests** (3 демо сценария)