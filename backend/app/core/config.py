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
    # Ücretsiz paket dakikada 10 istek kabul eder; istekler buna göre aralıklandırılır.
    api_football_requests_per_minute: int = 10

    default_league_id: int = 203  # Süper Lig; parametresiz sync ve CLI için
    default_season: int = 2024
    # Zamanlanmış sync'in takip ettiği ligler (API id'leri). Her biri default_season için
    # ayrı sync olarak, kota kontrolüyle çalışır. Kuralları rules/specs/leagues altında.
    tracked_leagues: list[int] = [203]

    cors_origins: list[str] = ["http://localhost:3000"]
    scheduler_enabled: bool = False
    sync_cron: str = "0 4 * * *"  # UTC; günde bir kez maçları güncelle (1 istek)
    # POST /sync/scheduled (dış cron, ör. GitHub Actions) bu değeri X-Sync-Token header'ında
    # ister. Boşsa o uç kapalıdır; arayüzün kullandığı POST /sync şifresizdir.
    sync_api_token: str = ""
    # Arayüzden elle güncelleme: aynı lig/sezon için iki güncelleme arasındaki en kısa süre.
    manual_sync_cooldown_minutes: int = 10
    sync_stale_after_minutes: int = 30  # bu süreden uzun RUNNING kalan sync çökmüş sayılır
    # Maç istatistikleri isteğe bağlı çekilir; günlük kotanın son N isteği sync'e ayrılır.
    statistics_quota_reserve: int = 10
    # Maç istatistikleri herkese açık bir uçtan istenir; günde en fazla bu kadar maç için çekilir.
    statistics_daily_limit: int = 30

    # AI karşılaştırma (Bonus C). Anahtar yoksa özellik kapalıdır.
    gemini_api_key: str = ""
    # Sırayla denenir: biri yoğunsa (429/503) sıradaki kullanılır.
    ai_models: list[str] = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]
    # Yedek sağlayıcı: Gemini başarısız olursa OpenRouter'daki modeller sırayla denenir.
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Ücretsiz modeller (2026-11 itibarıyla); Türkçe kalitesi ve hıza göre sıralı.
    openrouter_models: list[str] = [
        "google/gemma-4-26b-a4b-it:free",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
    ]
    ai_daily_limit: int = 50  # günde en fazla yeni analiz (önbellekten dönenler sayılmaz)
    ai_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
