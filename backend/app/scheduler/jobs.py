import logging
from collections.abc import Callable
from contextlib import AbstractContextManager

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.core.enums import SyncTrigger
from app.core.exceptions import AppError
from app.models import SyncRun
from app.providers.api_football.provider import build_api_football_provider
from app.providers.base import FootballDataProvider
from app.services.sync_service import SyncService

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], AbstractContextManager[Session]]
ProviderFactory = Callable[[Settings], AbstractContextManager[FootballDataProvider]]


def run_scheduled_sync(
    session_factory: SessionFactory = SessionLocal,
    provider_factory: ProviderFactory = build_api_football_provider,
    settings: Settings | None = None,
) -> list[SyncRun]:
    """Takip edilen her lig için günlük maç senkronizasyonu (lig başına en fazla 1 istek).

    Ligler sırayla ve birbirinden bağımsız çalışır: biri hata verse ya da kotaya takılsa
    diğerleri denenir. Scheduler thread'inde çalışır; hiçbir hata dışarı sızmaz.
    """
    settings = settings or get_settings()
    runs: list[SyncRun] = []
    for league in settings.tracked_leagues:
        if run := _sync_league(league, session_factory, provider_factory, settings):
            runs.append(run)
    return runs


def _sync_league(
    league: int,
    session_factory: SessionFactory,
    provider_factory: ProviderFactory,
    settings: Settings,
) -> SyncRun | None:
    try:
        with provider_factory(settings) as provider, session_factory() as session:
            run = SyncService(session, settings, provider).run(
                SyncTrigger.SCHEDULED, league_external_id=league, season=settings.default_season
            )
            logger.info("Zamanlanmış sync #%s (lig %s): %s", run.id, league, run.status)
            return run
    except AppError as exc:  # kota yetersiz, başka sync çalışıyor: beklenen durumlar
        logger.warning("Zamanlanmış sync atlandı (lig %s): %s", league, exc.message)
    except Exception:
        logger.exception("Zamanlanmış sync beklenmeyen hatayla bitti (lig %s)", league)
    return None
