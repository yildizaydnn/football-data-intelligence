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
) -> SyncRun | None:
    """Günlük maç senkronizasyonu (sadece /fixtures, 1 istek).

    Scheduler thread'inde çalışır; hiçbir hata dışarı sızmaz, aksi halde job sessizce ölür.
    """
    settings = settings or get_settings()
    try:
        with provider_factory(settings) as provider, session_factory() as session:
            run = SyncService(session, settings, provider).run(SyncTrigger.SCHEDULED)
            logger.info("Zamanlanmış sync #%s: %s", run.id, run.status)
            return run
    except AppError as exc:  # kota yetersiz, başka sync çalışıyor: beklenen durumlar
        logger.warning("Zamanlanmış sync atlandı: %s", exc.message)
    except Exception:
        logger.exception("Zamanlanmış sync beklenmeyen hatayla bitti")
    return None
