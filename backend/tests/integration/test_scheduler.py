from contextlib import contextmanager, nullcontext

import pytest
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SyncStatus, SyncTrigger
from app.repositories.api_usage_repository import ApiUsageRepository
from app.repositories.sync_repository import SyncRunRepository
from app.scheduler.jobs import run_scheduled_sync
from app.scheduler.setup import DAILY_SYNC_JOB_ID, create_scheduler, start_scheduler
from tests.fakes import FakeProvider


def _settings(**overrides) -> Settings:
    base = {
        "_env_file": None,
        "default_league_id": 203,
        "default_season": 2024,
        "api_football_daily_limit": 100,
        "api_football_key": "test-key",
    }
    return Settings(**(base | overrides))


class TestSchedulerSetup:
    def test_daily_job_uses_configured_cron(self) -> None:
        scheduler = create_scheduler(_settings(sync_cron="30 5 * * *"))

        job = scheduler.get_job(DAILY_SYNC_JOB_ID)

        assert isinstance(job.trigger, CronTrigger)
        assert str(job.trigger.fields[5]) == "5"  # hour
        assert str(job.trigger.fields[6]) == "30"  # minute
        assert job.max_instances == 1

    def test_not_started_when_disabled(self) -> None:
        assert start_scheduler(_settings(scheduler_enabled=False)) is None

    def test_not_started_without_api_key(self) -> None:
        assert start_scheduler(_settings(scheduler_enabled=True, api_football_key="")) is None

    def test_starts_and_stops(self) -> None:
        scheduler = start_scheduler(_settings(scheduler_enabled=True))
        try:
            assert scheduler is not None and scheduler.running
            assert scheduler.get_job(DAILY_SYNC_JOB_ID).next_run_time is not None
        finally:
            scheduler.shutdown(wait=False)


class TestScheduledSyncJob:
    @pytest.fixture
    def provider(self) -> FakeProvider:
        return FakeProvider()

    def _run(self, db_session: Session, provider: FakeProvider, **settings):
        @contextmanager
        def provider_factory(_settings):
            yield provider

        return run_scheduled_sync(
            session_factory=lambda: nullcontext(db_session),
            provider_factory=provider_factory,
            settings=_settings(**settings),
        )

    def test_creates_scheduled_run(self, db_session: Session, provider: FakeProvider) -> None:
        run = self._run(db_session, provider)

        assert run is not None
        assert run.trigger is SyncTrigger.SCHEDULED
        assert run.status is SyncStatus.PARTIAL

    def test_quota_exceeded_is_logged_not_raised(
        self, db_session: Session, provider: FakeProvider, caplog: pytest.LogCaptureFixture
    ) -> None:
        ApiUsageRepository(db_session).record(100, daily_limit=100)

        assert self._run(db_session, provider) is None
        assert provider.calls == []
        assert "Günlük API bütçesi yetersiz" in caplog.text

    def test_running_sync_is_logged_not_raised(
        self, db_session: Session, provider: FakeProvider, caplog: pytest.LogCaptureFixture
    ) -> None:
        SyncRunRepository(db_session).try_start(SyncTrigger.MANUAL)

        assert self._run(db_session, provider) is None
        assert "çalışan bir senkronizasyon" in caplog.text

    def test_unexpected_error_is_logged_not_raised(
        self, db_session: Session, caplog: pytest.LogCaptureFixture
    ) -> None:
        def broken_factory(_settings):
            raise RuntimeError("db down")

        result = run_scheduled_sync(
            session_factory=lambda: nullcontext(db_session),
            provider_factory=broken_factory,
            settings=_settings(),
        )

        assert result is None
        assert "beklenmeyen hata" in caplog.text
