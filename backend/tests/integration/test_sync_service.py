from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SyncStatus, SyncTrigger
from app.core.exceptions import ProviderError, SyncInProgressError
from app.models import Fixture, SyncRun, Team
from app.repositories.sync_repository import SyncRunRepository
from app.services.sync_service import SyncService
from tests.fakes import FakeProvider

SETTINGS = Settings(
    _env_file=None, default_league_id=203, default_season=2024, api_football_daily_limit=100
)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider(remaining=90)


@pytest.fixture
def service(db_session: Session, provider: FakeProvider) -> SyncService:
    return SyncService(db_session, SETTINGS, provider)


def test_first_sync_loads_data_and_records_run_and_usage(service: SyncService) -> None:
    run = service.run(SyncTrigger.INITIAL)

    # Örnek veride 1 bozuk maç (1006) var → PARTIAL, nedeni kayıtta
    assert run.status is SyncStatus.PARTIAL
    assert (run.requests_made, run.inserted, run.updated, run.skipped) == (3, 12, 0, 1)
    assert "#1006" in run.error_message
    assert run.finished_at is not None

    usage = service.get_usage()
    assert (usage.requests_used, usage.provider_remaining, usage.remaining) == (3, 87, 87)


def test_clean_data_gives_success(service: SyncService, provider: FakeProvider) -> None:
    provider.fixtures = [f for f in provider.fixtures if f["fixture"]["id"] != 1006]

    run = service.run(SyncTrigger.MANUAL)

    assert run.status is SyncStatus.SUCCESS
    assert run.error_message is None


def test_second_sync_updates_changed_fixture(
    service: SyncService, provider: FakeProvider, db_session: Session
) -> None:
    service.run(SyncTrigger.INITIAL)
    live = provider.fixture(1003)
    live["fixture"]["status"]["short"] = "FT"
    live["goals"] = {"home": 3, "away": 0}

    run = service.run(SyncTrigger.SCHEDULED)

    assert (run.requests_made, run.inserted, run.updated) == (1, 0, 1)
    assert service.get_usage().requests_used == 4


def test_provider_failure_marks_run_failed_and_rolls_back_data(
    service: SyncService, provider: FakeProvider, db_session: Session
) -> None:
    provider.fail_on["get_fixtures"] = ProviderError("API-Football HTTP 503", requests_made=3)

    run = service.run(SyncTrigger.MANUAL)

    assert run.status is SyncStatus.FAILED
    assert run.error_message == "API-Football HTTP 503"
    # /fixtures'tan önce yazılan lig/takım verisi de geri alındı
    assert db_session.query(Team).count() == 0
    assert db_session.query(Fixture).count() == 0
    # ama harcanan istekler (2 başarılı + 3 başarısız deneme) kotaya yazıldı
    assert run.requests_made == 5
    assert service.get_usage().requests_used == 5
    assert service.get_state().running is None


def test_unexpected_error_is_recorded_not_raised(
    service: SyncService, provider: FakeProvider
) -> None:
    provider.fail_on["get_teams"] = RuntimeError("bug")

    run = service.run(SyncTrigger.MANUAL)

    assert run.status is SyncStatus.FAILED
    assert "RuntimeError" in run.error_message


def test_concurrent_sync_is_rejected(service: SyncService, db_session: Session) -> None:
    SyncRunRepository(db_session).try_start(SyncTrigger.SCHEDULED)

    with pytest.raises(SyncInProgressError):
        service.run(SyncTrigger.MANUAL)


def test_stale_running_sync_is_released(service: SyncService, db_session: Session) -> None:
    stale = SyncRunRepository(db_session).try_start(SyncTrigger.SCHEDULED)
    db_session.execute(
        update(SyncRun)
        .where(SyncRun.id == stale.id)
        .values(started_at=datetime.now(UTC) - timedelta(hours=2))
    )

    run = service.run(SyncTrigger.MANUAL)

    db_session.refresh(stale)
    assert stale.status is SyncStatus.FAILED
    assert run.status is SyncStatus.PARTIAL
    assert [r.id for r in service.get_state().recent] == [run.id, stale.id]


def test_usage_reports_next_sync_cost(service: SyncService) -> None:
    before = service.get_usage()
    service.run(SyncTrigger.INITIAL)
    after = service.get_usage()

    assert (before.next_sync_cost, before.can_sync) == (3, True)  # lig/takımlar henüz yok
    assert after.next_sync_cost == 1


def test_schedule_reports_next_run_when_enabled(db_session: Session) -> None:
    settings = SETTINGS.model_copy(
        update={"scheduler_enabled": True, "api_football_key": "k", "sync_cron": "0 4 * * *"}
    )

    schedule = SyncService(db_session, settings).get_state().schedule

    assert schedule.enabled
    assert (schedule.next_run_at.hour, schedule.next_run_at.minute) == (4, 0)
    assert schedule.next_run_at > datetime.now(UTC)
