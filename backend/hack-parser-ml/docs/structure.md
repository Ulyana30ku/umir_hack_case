# Project Structure

```
hack-parser-ml/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py      # /health endpoint
│   │       └── agent.py       # /agent/run endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings configuration
│   │   └── logging.py         # Structured logging setup
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py          # Common DTOs
│   │   ├── query.py            # Query parsing schemas
│   │   ├── product.py          # Product schemas
│   │   ├── news.py             # News schemas
│   │   ├── trace.py            # Trace schemas
│   │   └── response.py         # Final response schemas
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Main orchestration
│   │   ├── planner.py          # Execution planner
│   │   ├── state.py            # Agent state
│   │   └── prompts.py          # LLM prompts
│   ├── services/
│   │   ├── __init__.py
│   │   ├── query_parser.py     # Query parsing service
│   │   ├── product_service.py  # Product search/extraction
│   │   ├── news_service.py     # News search/extraction
│   │   ├── ranking_service.py  # Ranking service
│   │   ├── validation_service.py # Validation service
│   │   └── answer_service.py   # Answer composition
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py             # Base tool interface
│   │   ├── product_search.py   # Product search tool
│   │   ├── product_extract.py  # Product extraction
│   │   ├── news_search.py      # News search tool
│   │   └── news_extract.py     # News extraction
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   └── client.py       # LLM client abstraction
│   │   ├── marketplaces/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Marketplace base
│   │   │   └── demo_marketplace.py # Demo marketplace
│   │   └── news/
│   │       ├── __init__.py
│   │       ├── base.py          # News source base
│   │       └── demo_news_source.py # Demo news source
│   └── utils/
│       ├── __init__.py
│       ├── text.py             # Text utilities
│       ├── normalization.py    # Normalization helpers
│       └── dates.py            # Date utilities
├── tests/
│   ├── __init__.py
│   ├── test_query_parser.py
│   ├── test_validation.py
│   ├── test_ranking.py
│   └── test_agent_flow.py
├── docs/
│   └── architecture.md         # Architecture docs
├── data/
│   ├── mock_products.json     # Demo product data
│   └── mock_news.json         # Demo news data
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## File Creation Order

1. `requirements.txt` - Dependencies
2. `.env.example` - Environment template
3. `app/core/config.py` - Configuration
4. `app/core/logging.py` - Logging setup
5. `app/schemas/*.py` - All Pydantic schemas
6. `app/core/__init__.py`, `app/schemas/__init__.py`, etc.
7. `app/main.py` - FastAPI app
8. `app/api/routes/health.py` - Health endpoint
9. `app/api/routes/agent.py` - Agent endpoint
10. All services
11. All tools and integrations
12. Tests
13. Docker files
14. README
