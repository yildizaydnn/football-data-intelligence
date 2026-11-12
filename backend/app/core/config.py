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

    default_league_id: int = 203  # Süper Lig; parametresiz sync ve CLI için
    default_season: int = 2024
    # Zamanlanmış sync'in takip ettiği ligler (API id'leri). Her biri default_season için
    # ayrı sync olarak, kota kontrolüyle çalışır. Kuralları rules/specs/leagues altında.
    tracked_leagues: list[int] = [203]

    cors_origins: list[str] = ["http://localhost:3000"]
    scheduler_enabled: bool = False
    sync_cron: str = "0 4 * * *"  # UTC; günde bir kez maçları güncelle (1 istek)
    # Doluysa POST /sync bu değeri X-Sync-Token header'ında ister (dış cron, prod ortamı).
    sync_api_token: str = ""
    sync_stale_after_minutes: int = 30  # bu süreden uzun RUNNING kalan sync çökmüş sayılır


@lru_cache
def get_settings() -> Settings:
    return Settings()
