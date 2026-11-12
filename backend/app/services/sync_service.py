import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SyncStatus, SyncTrigger
from app.core.exceptions import AppError, QuotaExceededError, SyncInProgressError
from app.etl.pipeline import PipelineResult, Repositories, SyncPipeline, estimate_requests
from app.models import SyncRun
from app.providers.base import FootballDataProvider
from app.repositories.api_usage_repository import ApiUsageRepository, utc_today
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.sync_repository import SyncRunRepository
from app.repositories.team_repository import TeamRepository

logger = logging.getLogger(__name__)

MAX_ERROR_LENGTH = 1000


@dataclass(frozen=True)
class SyncUsage:
    day: date
    requests_used: int
    daily_limit: int
    remaining: int  # bizim sayaç ile API header'ından küçük olanı
    provider_remaining: int | None
    next_sync_cost: int  # varsayılan lig/sezon için bir sonraki sync'in istek sayısı

    @property
    def can_sync(self) -> bool:
        return self.remaining >= self.next_sync_cost


@dataclass(frozen=True)
class SyncSchedule:
    enabled: bool
    cron: str  # UTC
    next_run_at: datetime | None


@dataclass(frozen=True)
class SyncState:
    running: SyncRun | None
    recent: list[SyncRun]
    schedule: SyncSchedule


class SyncService:
    """Sync iş akışının sahibi: kota kontrolü, kilit, pipeline, kayıt ve transaction sınırları."""

    def __init__(
        self,
        session: Session,
        settings: Settings,
        provider: FootballDataProvider | None = None,
    ) -> None:
        self.session = session
        self.provider = provider
        self.settings = settings
        self.sync_runs = SyncRunRepository(session)
        self.api_usage = ApiUsageRepository(session)
        self.repos = Repositories(
            leagues=LeagueRepository(session),
            seasons=SeasonRepository(session),
            teams=TeamRepository(session),
            fixtures=FixtureRepository(session),
        )

    def run(
        self,
        trigger: SyncTrigger,
        *,
        full: bool = False,
        league_external_id: int | None = None,
        season: int | None = None,
    ) -> SyncRun:
        """Sync'i çalıştırır ve sonuç kaydını döner.

        Başlamadan önce reddedilirse hata fırlatır (kota yetersiz, başka sync çalışıyor).
        Başladıktan sonraki hatalar fırlatılmaz; FAILED olarak kaydedilip run döner.
        """
        if self.provider is None:
            raise RuntimeError("SyncService.run için provider gerekli")
        league_external_id = league_external_id or self.settings.default_league_id
        season = season or self.settings.default_season
        pipeline = SyncPipeline(self.provider, self.repos)

        self._release_stale_runs()
        self._check_budget(pipeline.estimate_requests(league_external_id, season, full=full))

        run = self.sync_runs.try_start(trigger)
        if run is None:
            raise SyncInProgressError("Şu anda çalışan bir senkronizasyon var")
        self.session.commit()  # kilit diğer bağlantılara görünür olsun

        result: PipelineResult | None = None
        error: str | None = None
        try:
            result = pipeline.run(league_external_id, season, full=full, sync_run_id=run.id)
        except AppError as exc:
            error = exc.message
        except Exception as exc:
            logger.exception("Sync %s beklenmeyen hatayla bitti", run.id)
            error = f"Beklenmeyen hata: {exc!r}"

        if result is None:
            self.session.rollback()  # yarım kalan veri yazımlarını geri al
        self._record_usage(pipeline)
        self._finish(run, result, error, pipeline.requests_made)
        self.session.commit()
        logger.info("Sync %s bitti: %s", run.id, run.status)
        return run

    def get_state(self, recent: int = 10) -> SyncState:
        return SyncState(
            self.sync_runs.get_running(), self.sync_runs.list_recent(recent), self._schedule()
        )

    def get_usage(self) -> SyncUsage:
        limit = self.settings.api_football_daily_limit
        usage = self.api_usage.get_for_day()
        return SyncUsage(
            day=utc_today(),
            requests_used=usage.requests_used if usage else 0,
            daily_limit=limit,
            remaining=self.api_usage.remaining_budget(limit),
            provider_remaining=usage.remaining if usage else None,
            next_sync_cost=estimate_requests(
                self.repos,
                self.settings.default_league_id,
                self.settings.default_season,
                full=False,
            ),
        )

    def _schedule(self) -> SyncSchedule:
        enabled = self.settings.scheduler_enabled and bool(self.settings.api_football_key)
        next_run = None
        if enabled:
            trigger = CronTrigger.from_crontab(self.settings.sync_cron, timezone=UTC)
            next_run = trigger.get_next_fire_time(None, datetime.now(UTC))
        return SyncSchedule(enabled, self.settings.sync_cron, next_run)

    def _release_stale_runs(self) -> None:
        threshold = datetime.now(UTC) - timedelta(minutes=self.settings.sync_stale_after_minutes)
        if released := self.sync_runs.fail_stale(started_before=threshold):
            logger.warning("%d adet takılı kalmış sync FAILED olarak kapatıldı", released)
            self.session.commit()

    def _check_budget(self, needed: int) -> None:
        remaining = self.api_usage.remaining_budget(self.settings.api_football_daily_limit)
        if remaining < needed:
            raise QuotaExceededError(
                f"Günlük API bütçesi yetersiz: {needed} istek gerekiyor, {remaining} kaldı"
            )

    def _record_usage(self, pipeline: SyncPipeline) -> None:
        if pipeline.requests_made:
            self.api_usage.record(
                pipeline.requests_made,
                daily_limit=self.settings.api_football_daily_limit,
                remaining=pipeline.requests_remaining,
            )

    def _finish(
        self,
        run: SyncRun,
        result: PipelineResult | None,
        error: str | None,
        requests_made: int,
    ) -> None:
        if result is None:
            self.sync_runs.finish(
                run,
                SyncStatus.FAILED,
                requests_made=requests_made,
                error_message=(error or "")[:MAX_ERROR_LENGTH],
            )
            return

        skipped = len(result.skipped)
        self.sync_runs.finish(
            run,
            SyncStatus.PARTIAL if skipped else SyncStatus.SUCCESS,
            requests_made=requests_made,
            inserted=result.upsert.inserted,
            updated=result.upsert.updated,
            skipped=skipped,
            error_message=_summarize_skipped(result) if skipped else None,
        )


def _summarize_skipped(result: PipelineResult) -> str:
    lines = [f"{s.transformer} #{s.external_id}: {s.reason}" for s in result.skipped[:20]]
    if len(result.skipped) > 20:
        lines.append(f"... ve {len(result.skipped) - 20} kayıt daha")
    return "\n".join(lines)[:MAX_ERROR_LENGTH]
