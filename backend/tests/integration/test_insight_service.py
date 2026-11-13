import pytest
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import SyncTrigger
from app.core.exceptions import AiNotConfiguredError, BadRequestError, QuotaExceededError
from app.providers.llm.base import GeneratedText
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.team_repository import TeamRepository
from app.rules.engine import get_rule_engine
from app.services.insight_service import InsightService
from app.services.league_service import LeagueService
from app.services.sync_service import SyncService
from tests.fakes import FakeProvider

SETTINGS = Settings(_env_file=None, default_league_id=203, default_season=2024, ai_daily_limit=2)


class FakeGenerator:
    def __init__(self, text: str = "Galatasaray 0 puanda, Fenerbahçe 3 puanla önde.") -> None:
        self.text = text
        self.calls: list[str] = []

    def generate(self, *, system: str, prompt: str) -> GeneratedText:
        self.calls.append(prompt)
        return GeneratedText(self.text, "fake-model")


@pytest.fixture
def provider(db_session: Session) -> FakeProvider:
    provider = FakeProvider()
    SyncService(db_session, SETTINGS, provider).run(SyncTrigger.INITIAL)
    return provider


@pytest.fixture
def ids(db_session: Session, provider: FakeProvider) -> dict[str, int]:
    teams = TeamRepository(db_session)
    return {
        "league": LeagueRepository(db_session).get_by_external_id(203).id,
        "gs": teams.get_by_external_id(645).id,
        "fb": teams.get_by_external_id(611).id,
        "bjk": teams.get_by_external_id(549).id,
    }


def _service(db_session: Session, generator: FakeGenerator | None) -> InsightService:
    leagues = LeagueService(LeagueRepository(db_session), SeasonRepository(db_session))
    return InsightService(db_session, SETTINGS, leagues, get_rule_engine(), generator)


def test_generates_then_serves_from_cache(db_session: Session, ids: dict[str, int]) -> None:
    generator = FakeGenerator()
    service = _service(db_session, generator)

    first = service.compare(ids["league"], ids["gs"], ids["fb"])
    second = service.compare(ids["league"], ids["fb"], ids["gs"])  # ters sıra: aynı analiz

    assert len(generator.calls) == 1
    assert (first.cached, second.cached) == (False, True)
    assert first.model == "fake-model"
    assert first.unverified_numbers == []
    assert "Galatasaray 1-3 Fenerbahçe" in generator.calls[0]  # gerçek skor istemde
    assert (
        first.comparison.head_to_head.team_b_wins + first.comparison.head_to_head.team_a_wins == 1
    )


def test_regenerates_when_data_changes(
    db_session: Session, ids: dict[str, int], provider: FakeProvider
) -> None:
    generator = FakeGenerator()
    service = _service(db_session, generator)
    service.compare(ids["league"], ids["gs"], ids["fb"])

    live = provider.fixture(1003)  # FB - BJK canlı → bitti
    live["fixture"]["status"]["short"] = "FT"
    SyncService(db_session, SETTINGS, provider).run(SyncTrigger.MANUAL)
    again = service.compare(ids["league"], ids["fb"], ids["gs"])

    assert len(generator.calls) == 2  # FB'nin istatistikleri değişti → yeni analiz
    assert again.cached is False


def test_unverified_numbers_are_recorded(db_session: Session, ids: dict[str, int]) -> None:
    service = _service(db_session, FakeGenerator("Fenerbahçe 27 maçta 64 gol attı."))

    insight = service.compare(ids["league"], ids["gs"], ids["fb"])

    assert insight.unverified_numbers == ["27", "64"]


def test_daily_limit(db_session: Session, ids: dict[str, int]) -> None:
    service = _service(db_session, FakeGenerator())
    service.compare(ids["league"], ids["gs"], ids["fb"])
    service.compare(ids["league"], ids["gs"], ids["bjk"])

    with pytest.raises(QuotaExceededError):
        service.compare(ids["league"], ids["fb"], ids["bjk"])
    assert service.status().generated_today == 2


def test_disabled_without_api_key(db_session: Session, ids: dict[str, int]) -> None:
    service = _service(db_session, None)

    assert service.status().enabled is False
    with pytest.raises(AiNotConfiguredError):
        service.compare(ids["league"], ids["gs"], ids["fb"])


def test_invalid_team_pairs(db_session: Session, ids: dict[str, int]) -> None:
    service = _service(db_session, FakeGenerator())

    with pytest.raises(BadRequestError, match="farklı"):
        service.compare(ids["league"], ids["gs"], ids["gs"])
    with pytest.raises(BadRequestError, match="sezonda"):
        service.compare(ids["league"], ids["gs"], 999_999)
    assert FixtureRepository(db_session).count() > 0
