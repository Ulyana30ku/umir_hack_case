# Architecture: AI Browser Assistant

## Overview

**Universal Browser Agent** - система управления браузером через естественный язык.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                  │
│         "зайди на ozon, найди iPhone 15 Pro и верни цену"         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API LAYER (FastAPI)                           │
│   POST /agent/run  │  GET /agent/run/{id}  │  GET /agent/trace     │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      AGENT / ORCHESTRATOR                           │
│   - Координирует выполнение                                         │
│   - Управляет состоянием (state machine)                           │
│   - Логирует trace                                                  │
│   - Обрабатывает ошибки и failover                                 │
└─────────────────────────────────────────────────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  QUERY PARSER    │    │     PLANNER      │    │ TOOL REGISTRY    │
│                  │    │                  │    │                  │
│ - Intent detect  │    │ - Plan creation │    │ - browser_*      │
│ - Entity extract │    │ - Tool selection│    │ - data tools     │
│ - Intent:        │    │ - Step ordering │    │ - domain tools   │
│   * navigation   │    │                 │    │                  │
│   * interaction  │    │                 │    │                  │
│   * info_retriev │    │                 │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                                      │
                              ┌───────────────────────┴────────────────────┐
                              ▼                                            ▼
              ┌──────────────────────────────┐          ┌──────────────────────────────┐
              │    BROWSER TOOLS            │          │     DATA TOOLS               │
              │                              │          │                              │
              │ - browser_open_url()        │          │ - search_products()          │
              │ - browser_click()           │          │ - search_news()              │
              │ - browser_type()            │          │ - extract_product_fields()   │
              │ - browser_scroll()          │          │ - extract_news_items()       │
              │ - browser_wait_*()          │          │ - validate_product()         │
              │ - browser_get_*()            │          │ - rank_*()                   │
              └──────────────────────────────┘          └──────────────────────────────┘
                              │                                            │
                              ▼                                            ▼
              ┌──────────────────────────────────────────────────────┐
              │           BROWSER AUTOMATION (Playwright)            │
              │   - BrowserSessionManager                            │
              │   - Page actions (click, type, scroll)                │
              │   - DOM extraction                                    │
              │   - Screenshots on error                             │
              └──────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Layer
- **FastAPI endpoints** - `/agent/run`, `/agent/status`, `/agent/trace`
- Request/response validation via Pydantic
- Async execution

### 2. Query Parser
- **Intent Classification**: navigation, interaction, info_retrieval, product_search, news_search, multi_step
- **Entity Extraction**: url, query, button_text, constraints
- **Execution Hints**: requires_browser, requires_extraction, multi_step

### 3. Planner
- Детерминированный
- На основе intent_type создает последовательность tool calls
- Обрабатывает multi-step сценарии

### 4. Tool Registry
- Единый интерфейс для всех tools
- Каждый tool: name, description, input_schema, output_schema, execute()
- Browser tools + Data tools + Domain tools

### 5. Browser Automation (Playwright)
- **BrowserSessionManager**: create/close/reuse sessions
- **Tools**: open_url, click, type, scroll, wait, extract
- Headless/headful support
- Error handling + screenshots

### 6. Data Tools
- RSS news (real data)
- Product search (browser-based or fallback to API)
- Validation, ranking, answer composing

### 7. Trace
- Полное логирование каждого шага
- Tool input/output
- Browser URL + screenshots
- Error tracking

## Data Flow

```
User Query
    │
    ▼
Query Parser → Intent Classification + Entities
    │
    ▼
Planner → Execution Plan (sequence of tool calls)
    │
    ▼
For each step in plan:
    │
    ├─► ToolRegistry → get_tool(name)
    │
    ├─► Tool.execute(input)
    │
    ├─► If browser tool: → Playwright execution
    │
    ├─► Log step to trace
    │
    └─► Continue or abort
    │
    ▼
Compose final response + trace
```

## Supported Task Types

| Task Type | Description | Example |
|-----------|-------------|---------|
| `browser_navigation` | Открыть URL | "зайди на example.com" |
| `browser_interaction` | Действия в браузере | "введи в поиске iPhone" |
| `info_retrieval` | Извлечение данных | "верни заголовок страницы" |
| `product_search` | Поиск товара | "найди iPhone 15 Pro" |
| `news_search` | Поиск новостей | "новости про AI" |
| `multi_step` | Составные задачи | "открой сайт, найди, собери данные" |

## Demo Scenarios

1. **Navigation**: "зайди на example.com и верни заголовок"
2. **Interaction**: "зайди в поисковик, введи iPhone 15 и открой первый результат"
3. **Product + News**: "найди iPhone 15 Pro 256GB и собери новости про Apple"

## Tech Stack

- Python 3.11+
- FastAPI
- Pydantic
- Playwright (browser automation)
- httpx (HTTP client)
- pytest (tests)

## Environment

- `REAL_ONLY=true` - использовать только реальные источники
- `OPENAI_API_KEY` - опционально для LLM assistance
- RSS sources: iXBT, 3DNews, Habr, Nplus1
