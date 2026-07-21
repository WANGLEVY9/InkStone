"""Application configuration settings loaded from environment variables.

Pydantic model for all runtime configuration, with sensible defaults
for local development.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via a ``.env`` file or environment
    variables. Fields that are empty strings (e.g. API keys) must be
    provided at runtime for features that require them.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = Field(default="Novel Generator", description="Human-readable application name.")
    DEBUG: bool = Field(default=False, description="Enable verbose debug logging.")
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origin list.",
    )

    # LLM Provider
    LLM_PROVIDER: str = Field(default="anthropic", description="LLM provider name (e.g. anthropic, openai).")
    LLM_BASE_URL: str | None = Field(default=None, description="Optional base URL for LLM API endpoint.")
    LLM_MODEL: str = Field(default="claude-sonnet-4-20250514", description="Model identifier for the LLM.")
    ANTHROPIC_API_KEY: str = Field(default="", description="API key for the LLM provider.")

    # SQLite Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./novel.db",
        description="SQLAlchemy database connection string.",
    )


settings = Settings()
