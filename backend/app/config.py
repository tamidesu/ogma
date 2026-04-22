from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str
    app_debug: bool = False
    app_cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_session_ttl: int = 1800       # seconds
    redis_refresh_token_ttl: int = 604800  # seconds

    # Auth
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Groq AI
    groq_api_key: str
    groq_default_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-8b-instant"
    groq_max_tokens: int = 1024
    groq_temperature: float = 0.7
    groq_timeout: int = 30

    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20

    # Features
    rag_enabled: bool = True               # BM25 RAG is free — enabled by default
    ai_feedback_async: bool = True
    ai_structured_output: bool = True      # Use Groq JSON mode for rich feedback
    ai_stream_feedback: bool = False       # Stream via SSE (set True when frontend ready)
    ai_feedback_history_depth: int = 5    # How many past decisions to include in prompt

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    @field_validator("app_cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
