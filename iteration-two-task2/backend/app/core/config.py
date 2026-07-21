from functools import lru_cache
from typing import List

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "agent-eval-platform"
    env: str = "dev"
    api_prefix: str = "/api/v1"

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_db: str = "agent_eval"
    mysql_user: str = "root"
    mysql_password: str = "root"
    database_url: str | None = None

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "agent_eval"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    cors_origins: str = "http://localhost:5173"
    use_celery: bool = False
    ragas_enabled: bool = True

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    llm_judge_model: str = "gpt-4o-mini"

    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_llm_model: str = "deepseek-chat"
    upload_dir: str = "./uploads"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> List[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
