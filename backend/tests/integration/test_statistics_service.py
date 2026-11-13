import copy

import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SyncTrigger
from app.core.exceptions import ProviderError, QuotaExceededError, TooManyRequestsError
from app.repositories.api_usage_repository import ApiUsageRepository
from app.repositories.fixture_repository import FixtureRepository
from app.rules.engine import get_rule_engine
from app.services.statistics_service import StatisticsAvailability, StatisticsService
from app.services.sync_service import SyncService
from tests.conftest import load_json
from tests.fakes import FakeProvider

SETTINGS = Settings(
    _env_file=None,
    default_league_id=203,
    default_season=2024,
    api_football_daily_limit=100,
    statistics_quota_reserve=10,
)


@pytest.fixture
def provider(db_session: Session) -> FakeProvider:
    provider = FakeProvider()
    SyncService(db_session, SETTINGS, provider).run(SyncTrigger.INITIAL)
    # Gerçek yanıt GS - Başakşehir; örnek maç 1001 GS - FB olduğu için deplasman takımını eşle.
    response = copy.deepcopy(load_json("statistics.json")["response"])
    response[1]["team"]["id"] = 611
    provider.statistics[1001] = response
    provider.calls.clear()
    return provider


@pytest.fixture
def service(db_session: Session, provider: FakeProvider) -> StatisticsService:
    return StatisticsService(db_session, SETTINGS, get_rule_engine(), provider)


def _fixture_id(db_session: Session, external_id: int) -> int:
    return FixtureRepository(db_session).get_by_external_id(external_id).id


def _used(db_session: Session) -> int:
    usage = ApiUsageRepository(db_session).get_for_day()
    return usage.requests_used if usage else 0


def test_fetched_once_then_served_from_db(
    service: StatisticsService, provider: FakeProvider, db_session: Session
) -> None:
    fixture_id = _fixture_id(db_session, 1001)
    before = _used(db_session)

    first = service.get(fixture_id)
    second = service.get(fixture_id)

    assert provider.calls == ["get_fixture_statistics"]
    assert _used(db_session) == before + 1
    assert first.availability is StatisticsAvailability.AVAILABLE
    lines = {line.key: (line.home, line.away) for line in second.lines}
    assert lines["possession"] == (59.0, 41.0)
    assert lines["expected_goals"] == (3.04, 1.24)
    assert [line.key for line in second.lines][:2] == [
        "possession",
        "expected_goals",
    ]  # spec sırası


def test_unavailable_is_remembered(
    service: StatisticsService, provider: FakeProvider, db_session: Session
) -> None:
    fixture_id = _fixture_id(db_session, 1002)  # sağlayıcıda istatistik yok

    first = service.get(fixture_id)
    service.get(fixture_id)

    assert first.availability is StatisticsAvailability.UNAVAILABLE
    assert first.fetched_at is not None
    assert provider.calls == ["get_fixture_statistics"]  # ikinci kez istenmedi


def test_unfinished_match_is_not_fetched(
    service: StatisticsService, provider: FakeProvider, db_session: Session
) -> None:
    result = service.get(_fixture_id(db_session, 1004))  # planlanmış maç

    assert result.availability is StatisticsAvailability.NOT_FINISHED
    assert provider.calls == []


def test_quota_reserve_protects_scheduled_syncs(
    service: StatisticsService, provider: FakeProvider, db_session: Session
) -> None:
    ApiUsageRepository(db_session).record(100 - 10 - _used(db_session), daily_limit=100)

    with pytest.raises(QuotaExceededError, match="otomatik güncellemelere"):
        service.get(_fixture_id(db_session, 1001))

    assert provider.calls == []


def test_provider_error_counts_requests_and_allows_retry(
    service: StatisticsService, provider: FakeProvider, db_session: Session
) -> None:
    fixture_id = _fixture_id(db_session, 1001)
    before = _used(db_session)
    provider.fail_on["get_fixture_statistics"] = ProviderError("HTTP 500", requests_made=3)

    with pytest.raises(ProviderError):
        service.get(fixture_id)
    assert _used(db_session) == before + 3

    del provider.fail_on["get_fixture_statistics"]
    assert service.get(fixture_id).availability is StatisticsAvailability.AVAILABLE


def test_daily_limit_caps_fetches(
    db_session: Session, provider: FakeProvider, service: StatisticsService
) -> None:
    capped = StatisticsService(
        db_session,
        SETTINGS.model_copy(update={"statistics_daily_limit": 1}),
        get_rule_engine(),
        provider,
    )
    capped.get(_fixture_id(db_session, 1001))  # günün ilk ve tek hakkı
    provider.calls.clear()

    with pytest.raises(TooManyRequestsError, match="yarın"):
        capped.get(_fixture_id(db_session, 1002))

    assert provider.calls == []
    assert service.get(_fixture_id(db_session, 1001)).lines  # çekilmiş olan yine okunur


def test_fetch_done_while_waiting_for_lock_is_not_repeated(
    db_session: Session, provider: FakeProvider, service: StatisticsService
) -> None:
    from datetime import UTC, datetime

    from sqlalchemy import update

    from app.models import Fixture

    fixture_id = _fixture_id(db_session, 1001)
    FixtureRepository(db_session).get(fixture_id)  # nesne oturumda "çekilmemiş" haliyle
    # Eşzamanlı başka bir istek çekip damgaladı (ORM nesnesini güncellemeden, doğrudan SQL).
    db_session.execute(
        update(Fixture)
        .where(Fixture.id == fixture_id)
        .values(statistics_fetched_at=datetime.now(UTC))
        .execution_options(synchronize_session=False)
    )

    service.get(fixture_id)

    assert provider.calls == []  # kilitten sonra güncel satır okundu, tekrar çekilmedi
