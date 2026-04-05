# AI Browser Assistant

Универсальный AI ассистент для управления браузером через естественный язык.

## Описание

Система принимает запросы на русском языке и выполняет действия в браузере:
- Открывает страницы
- Вводит текст и кликает
- Скроллит и ждет загрузки
- Извлекает данные со страниц
- Выполняет многошаговые сценарии

## Multi-turn контекст (MVP)

Чат работает в рамках `session_id` и хранит историю сообщений в БД.

- Роли сообщений: `user` / `assistant` / `system`
- При новом сообщении backend:
  1) сохраняет `user` сообщение
  2) достаёт последние сообщения сессии (контекст)
  3) передаёт контекст + текущий запрос в orchestrator/agent
  4) сохраняет ответ `assistant`
  5) возвращает `assistant_message` и `recent_messages`
- Окно контекста ограничено последними сообщениями (по умолчанию до 20), чтобы контекст не разрастался бесконечно.

Пример multi-turn сценария:
1. «Открой Яндекс Маркет»
2. «Теперь найди там iPhone»
3. «Отсортируй по цене»

Следующие сообщения учитывают предыдущие шаги в пределах одной сессии.

Товары и новости — это примеры использования (частные сценарии поверх универсального browser agent).

## Архитектура

```
USER QUERY
    │
    ▼
┌─────────────────────────────────────────────┐
│  Query Parser (Intent Classification)       │
│  - navigation / interaction / info_retrieval│
│  - product_search / news_search / multi_step │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Planner (Execution Plan)                   │
│  - детерминированный план шагов             │
│  - выбор browser tools                      │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Tool Registry + Browser Automation         │
│  - Playwright for real browser actions      │
│  - open_url, click, type, scroll, wait      │
│  - get_text, get_links, screenshot          │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  Response + Trace                           │
│  - результат + объяснение + лог шагов      │
└─────────────────────────────────────────────┘
```

## Поддерживаемые типы задач

| Тип | Пример | Описание |
|-----|--------|----------|
| `browser_navigation` | "зайди на example.com" | Открыть URL |
| `browser_interaction` | "введи в поиске iPhone" | Действия в браузере |
| `info_retrieval` | "верни заголовок страницы" | Извлечение данных |
| `product_search` | "найди iPhone 15 Pro" | Поиск товара |
| `news_search` | "новости про AI" | Поиск новостей |
| `multi_step` | "открой сайт, найди, собери данные" | Составные задачи |

## Установка

```bash
# Установить зависимости
pip install -r requirements.txt

# Установить Playwright browsers
playwright install chromium
```

## Запуск

```bash
# Docker
docker-compose up --build

# Или локально
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health` - Health check
- `GET /agent/version` - Версия API
- `GET /agent/capabilities` - Возможности агента
- `POST /agent/run` - Запустить агента с запросом
- `GET /agent/run/{run_id}/trace` - Получить trace выполнения

## Примеры запросов

```bash
# Browser navigation
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"query": "зайди на example.com и верни заголовок страницы"}'

# Product search  
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"query": "найди iPhone 15 Pro 256GB"}'

# Multi-step
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"query": "зайди на ozon, найди iPhone и собери новости про Apple"}'
```

## Переменные окружения

```env
# OpenAI (опционально)
OPENAI_API_KEY=your-key

# Browser
HEADLESS=true

# Cache
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

## Demo сценарии

1. **Navigation**: "зайди на example.com и верни заголовок"
2. **Interaction**: "зайди в поисковик, введи iPhone 15 и открой первый результат"
3. **Product + News**: "найди iPhone 15 Pro 256GB и собери новости про Apple"

## Tech Stack

- Python 3.11+
- FastAPI
- Playwright (browser automation)
- Pydantic
