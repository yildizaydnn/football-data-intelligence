import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SyncTrigger
from app.core.exceptions import QuotaExceededError
from app.models import SyncRun
from app.repositories.api_usage_repository import ApiUsageRepository
from app.services.sync_service import SyncService
from tests.fakes import FakeProvider


def _settings(daily_limit: int) -> Settings:
    return Settings(
        _env_file=None,
        default_league_id=203,
        default_season=2024,
        api_football_daily_limit=daily_limit,
    )


def test_no_request_is_made_when_budget_is_insufficient(db_session: Session) -> None:
    provider = FakeProvider()
    service = SyncService(db_session, _settings(daily_limit=2), provider)  # ilk sync 3 ister

    with pytest.raises(QuotaExceededError, match="3 istek gerekiyor, 2 kaldı"):
        service.run(SyncTrigger.MANUAL)

    assert provider.calls == []
    assert db_session.query(SyncRun).count() == 0


def test_budget_accounts_for_requests_already_used_today(db_session: Session) -> None:
    ApiUsageRepository(db_session).record(98, daily_limit=100)
    provider = FakeProvider()

    with pytest.raises(QuotaExceededError):
        SyncService(db_session, _settings(100), provider).run(SyncTrigger.MANUAL)

    assert provider.calls == []


def test_budget_respects_lower_remaining_reported_by_api(db_session: Session) -> None:
    # Bizim sayacımıza göre 99 hak var ama API anahtarın başka yerde harcandığını bildiriyor.
    ApiUsageRepository(db_session).record(1, daily_limit=100, remaining=2)
    provider = FakeProvider()

    with pytest.raises(QuotaExceededError):
        SyncService(db_session, _settings(100), provider).run(SyncTrigger.MANUAL)

    assert provider.calls == []


def test_incremental_sync_fits_into_small_budget(db_session: Session) -> None:
    provider = FakeProvider()
    service = SyncService(db_session, _settings(daily_limit=4), provider)
    service.run(SyncTrigger.INITIAL)  # 3 istek → 1 hak kaldı
    provider.calls.clear()

    run = service.run(SyncTrigger.SCHEDULED)  # sadece /fixtures → 1 istek

    assert provider.calls == ["get_fixtures"]
    assert run.requests_made == 1
    assert service.get_usage().remaining == 0

    with pytest.raises(QuotaExceededError):
        service.run(SyncTrigger.MANUAL)


def _finish_all(provider: FakeProvider) -> None:
    """Sezonu bitmiş hale getirir: tüm maçlar FT ve skorlu."""
    for item in provider.fixtures:
        item["fixture"]["status"]["short"] = "FT"
        item["goals"] = {"home": item["goals"]["home"] or 1, "away": item["goals"]["away"] or 0}


class TestUnnecessaryRequests:
    def test_scheduled_sync_is_skipped_when_season_is_finished(self, db_session: Session) -> None:
        provider = FakeProvider()
        _finish_all(provider)
        service = SyncService(db_session, _settings(100), provider)
        service.run(SyncTrigger.INITIAL)
        provider.calls.clear()

        run = service.run(SyncTrigger.SCHEDULED)

        assert provider.calls == []
        assert run.status.value == "skipped"
        assert run.requests_made == 0
        assert "tüm maçlar sonuçlandı" in run.error_message
        assert service.get_usage().requests_used == 3  # sadece ilk yükleme

    def test_manual_sync_is_never_skipped(self, db_session: Session) -> None:
        provider = FakeProvider()
        _finish_all(provider)
        service = SyncService(db_session, _settings(100), provider)
        service.run(SyncTrigger.INITIAL)
        provider.calls.clear()

        service.run(SyncTrigger.MANUAL)

        assert provider.calls == ["get_fixtures"]

    def test_scheduled_sync_runs_while_matches_are_pending(self, db_session: Session) -> None:
        provider = FakeProvider()  # örnek veride planlanmış/canlı/ertelenmiş maçlar var
        service = SyncService(db_session, _settings(100), provider)
        service.run(SyncTrigger.INITIAL)
        provider.calls.clear()

        run = service.run(SyncTrigger.SCHEDULED)

        assert provider.calls == ["get_fixtures"]
        assert run.status.value != "skipped"

    def test_first_scheduled_sync_is_not_skipped(self, db_session: Session) -> None:
        provider = FakeProvider()
        _finish_all(provider)

        run = SyncService(db_session, _settings(100), provider).run(SyncTrigger.SCHEDULED)

        assert provider.calls == ["get_league", "get_teams", "get_fixtures"]
        assert run.status.value != "skipped"

    def test_skipped_run_does_not_block_next_sync(self, db_session: Session) -> None:
        provider = FakeProvider()
        _finish_all(provider)
        service = SyncService(db_session, _settings(100), provider)
        service.run(SyncTrigger.INITIAL)
        service.run(SyncTrigger.SCHEDULED)

        assert service.get_state().running is None
        run = service.run(SyncTrigger.MANUAL)
        assert run.status.value in ("success", "partial")  # örnek veride 1 bozuk kayıt var
        assert run.requests_made == 1
