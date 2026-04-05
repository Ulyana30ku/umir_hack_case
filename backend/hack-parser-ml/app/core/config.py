"""Application configuration using Pydantic Settings."""

from typing import Optional

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal environments
    from pydantic import BaseModel

    class SettingsConfigDict(dict):
        """Fallback config container when pydantic-settings is unavailable."""

    class BaseSettings(BaseModel):
        """Fallback base settings model."""

        model_config = SettingsConfigDict()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


    openai_api_key: str = "sk-your-api-key-here"
    openai_base_url: str = "https://api.openai.com/v1"


    app_name: str = "Hack Parser ML"
    app_version: str = "1.0.0"
    debug: bool = False

    log_level: str = "INFO"


    real_only: bool = False
    

    allow_partial_results: bool = True
    

    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour default
    

    max_retries: int = 4
    retry_base_delay: float = 1.0  # seconds
    retry_max_delay: float = 60.0  # seconds


    agent_execution_timeout_seconds: float = 180.0
    

    rate_limit_per_source: int = 2
    rate_limit_window: float = 1.0  # seconds
    

    news_source_1: str = "https://www.ixbt.com/rss/news.xml"
    news_source_2: str = "https://3dnews.ru/robots.txt"
    news_source_3: str = "https://habr.com/ru/rss/news/"
    news_source_4: str = "https://nplus1.ru/rss"
    

    max_news_items: int = 10
    max_product_candidates: int = 5
    request_delay_min: float = 0.5
    request_delay_max: float = 1.5



settings = Settings()
