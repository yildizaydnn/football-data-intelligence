"""İlk tam veri yükleme (CLI).

Kullanım:
    uv run python -m scripts.initial_sync            # .env'deki lig/sezon, tam yükleme
    uv run python -m scripts.initial_sync --season 2023
    uv run python -m scripts.initial_sync --fixtures-only
"""

import argparse
import sys

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.enums import SyncStatus, SyncTrigger
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.providers.api_football.provider import build_api_football_provider
from app.services.sync_service import SyncService


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="API-Football'dan veri senkronizasyonu")
    parser.add_argument("--league", type=int, default=settings.default_league_id)
    parser.add_argument("--season", type=int, default=settings.default_season)
    parser.add_argument(
        "--fixtures-only", action="store_true", help="Lig/takımları yenileme (1 istek)"
    )
    args = parser.parse_args()

    setup_logging(settings.log_level)
    if not settings.api_football_key:
        print("API_FOOTBALL_KEY tanımlı değil (.env)", file=sys.stderr)
        return 2

    with build_api_football_provider(settings) as provider, SessionLocal() as session:
        service = SyncService(session, settings, provider)
        try:
            run = service.run(
                SyncTrigger.INITIAL if not args.fixtures_only else SyncTrigger.MANUAL,
                full=not args.fixtures_only,
                league_external_id=args.league,
                season=args.season,
            )
        except AppError as exc:
            print(f"Sync başlatılamadı: {exc.message}", file=sys.stderr)
            return 1

        usage = service.get_usage()
        print(
            f"Sync #{run.id}: {run.status} | istek={run.requests_made} "
            f"eklenen={run.inserted} güncellenen={run.updated} atlanan={run.skipped}"
        )
        print(f"Bugünkü kullanım: {usage.requests_used}/{usage.daily_limit}")
        print(f"Kalan istek: {usage.remaining}")
        if run.error_message:
            print(f"Not: {run.error_message}")
        return 0 if run.status in (SyncStatus.SUCCESS, SyncStatus.PARTIAL) else 1


if __name__ == "__main__":
    sys.exit(main())
