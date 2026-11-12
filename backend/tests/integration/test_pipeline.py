import pytest
from sqlalchemy.orm import Session

from app.core.enums import MatchStatus
from app.core.exceptions import ProviderError
from app.etl.pipeline import Repositories, SyncPipeline
from app.repositories.base import UpsertResult
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.team_repository import TeamRepository
from app.rules.engine import get_rule_engine
from tests.fakes import FakeProvider

LEAGUE, SEASON = 203, 2024


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider(remaining=90)


@pytest.fixture
def repos(db_session: Session) -> Repositories:
    return Repositories(
        leagues=LeagueRepository(db_session),
        seasons=SeasonRepository(db_session),
        teams=TeamRepository(db_session),
        fixtures=FixtureRepository(db_session),
    )


@pytest.fixture
def pipeline(provider: FakeProvider, repos: Repositories) -> SyncPipeline:
    return SyncPipeline(provider, repos, get_rule_engine())


def test_first_run_loads_reference_and_fixtures(
    pipeline: SyncPipeline, provider: FakeProvider, repos: Repositories
) -> None:
    assert pipeline.estimate_requests(LEAGUE, SEASON, full=False) == 3

    result = pipeline.run(LEAGUE, SEASON)

    assert provider.calls == ["get_league", "get_teams", "get_fixtures"]
    # 1 lig + 2 sezon + 4 takım + 5 maç (1006 atlandı)
    assert result.upsert == UpsertResult(inserted=12)
    assert [s.external_id for s in result.skipped] == [1006]
    assert repos.fixtures.count() == 5
    assert (pipeline.requests_made, pipeline.requests_remaining) == (3, 87)


def test_second_run_only_fetches_fixtures_and_is_idempotent(
    pipeline: SyncPipeline, provider: FakeProvider
) -> None:
    pipeline.run(LEAGUE, SEASON)
    provider.calls.clear()

    assert pipeline.estimate_requests(LEAGUE, SEASON, full=False) == 1
    result = pipeline.run(LEAGUE, SEASON)

    assert provider.calls == ["get_fixtures"]
    assert result.upsert == UpsertResult(unchanged=5)


def test_score_update_is_written_with_history(
    pipeline: SyncPipeline, provider: FakeProvider, repos: Repositories
) -> None:
    pipeline.run(LEAGUE, SEASON)
    live = provider.fixture(1003)
    live["fixture"]["status"]["short"] = "FT"
    live["goals"] = {"home": 3, "away": 1}

    result = pipeline.run(LEAGUE, SEASON, sync_run_id=None)

    assert result.upsert == UpsertResult(updated=1, unchanged=4)
    fixture = repos.fixtures.get_by_external_id(1003)
    changes = {c.field: (c.old_value, c.new_value) for c in repos.fixtures.list_changes(fixture.id)}
    assert changes == {
        "status": ("live", "finished"),
        "home_goals": ("2", "3"),
        "away_goals": ("0", "1"),
    }
    assert repos.fixtures.list_finished(fixture.season_id)[-1].status is MatchStatus.FINISHED


def test_full_run_refreshes_reference(pipeline: SyncPipeline, provider: FakeProvider) -> None:
    pipeline.run(LEAGUE, SEASON)
    provider.calls.clear()

    pipeline.run(LEAGUE, SEASON, full=True)

    assert provider.calls == ["get_league", "get_teams", "get_fixtures"]


def test_requests_are_counted_even_when_provider_fails(
    pipeline: SyncPipeline, provider: FakeProvider
) -> None:
    provider.fail_on["get_fixtures"] = ProviderError("boom", requests_made=3)

    with pytest.raises(ProviderError):
        pipeline.run(LEAGUE, SEASON)

    assert pipeline.requests_made == 2 + 3
