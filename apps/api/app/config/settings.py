"""
Application Settings & Configuration Management.
Configures database, security, crawler limits, LLM providers, and observability.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    APP_NAME: str = "WebLens AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "*",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "https://weblens-ai-two.vercel.app",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./weblens.db"
    DATABASE_ECHO: bool = False

    # Security & SSRF Limits
    ALLOWED_SCHEMES: List[str] = ["http", "https"]
    ALLOWED_PORTS: List[int] = [80, 443, 8080, 8443]
    MAX_REDIRECTS: int = 5
    REQUEST_TIMEOUT_SECONDS: float = 15.0
    TOTAL_CRAWL_TIMEOUT_SECONDS: float = 60.0
    MAX_RESPONSE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    MAX_PAGES_PER_WEBSITE: int = 20
    MAX_CRAWL_DEPTH: int = 2
    USER_AGENT: str = "WebLensAI-AgenticBot/1.0 (+https://weblens.ai/bot; security@weblens.ai)"

    # Rate Limiting
    RATE_LIMIT_ANALYSIS_PER_MINUTE: int = 10
    RATE_LIMIT_CHAT_PER_MINUTE: int = 30

    # Agent Limits
    MAX_TOOL_CALLS: int = 8
    MAX_HISTORY_MESSAGES: int = 10

    # LLM Provider Configuration
    LLM_PROVIDER: str = "mock"  # mock | openai | gemini | grok | anthropic
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    XAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None
    GROK_MODEL: str = "grok-beta"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536


settings = Settings()
