from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Football Data Intelligence API"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://football:football@localhost:5433/football"

    api_football_base_url: str = "https://v3.football.api-sports.io"
    api_football_key: str = ""
    api_football_daily_limit: int = 100
    api_football_timeout_seconds: float = 10.0
    api_football_max_attempts: int = 3

    default_league_id: int = 203  # Süper Lig
    default_season: int = 2024

    cors_origins: list[str] = ["http://localhost:3000"]
    scheduler_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
