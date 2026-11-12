from dataclasses import dataclass
from datetime import datetime

from app.core.enums import MatchStatus, SortOrder
from app.core.exceptions import NotFoundError
from app.models import Fixture, FixtureChange
from app.repositories.fixture_repository import FixtureRepository
from app.services.league_service import LeagueService


@dataclass(frozen=True)
class FixtureFilters:
    status: MatchStatus | None = None
    team_id: int | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    order: SortOrder = SortOrder.ASC


@dataclass(frozen=True)
class FixturePage:
    items: list[Fixture]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class FixtureDetail:
    fixture: Fixture
    changes: list[FixtureChange]


class FixtureService:
    def __init__(self, fixtures: FixtureRepository, leagues: LeagueService) -> None:
        self.fixtures = fixtures
        self.leagues = leagues

    def list_fixtures(
        self,
        league_id: int,
        season_year: int | None,
        filters: FixtureFilters,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> FixturePage:
        season = self.leagues.resolve_season(league_id, season_year)
        items, total = self.fixtures.list_filtered(
            season.id,
            status=filters.status,
            team_id=filters.team_id,
            date_from=filters.date_from,
            date_to=filters.date_to,
            order=filters.order,
            limit=limit,
            offset=offset,
        )
        return FixturePage(items, total, limit, offset)

    def get_fixture(self, fixture_id: int) -> FixtureDetail:
        fixture = self.fixtures.get_with_teams(fixture_id)
        if fixture is None:
            raise NotFoundError(f"Maç bulunamadı: {fixture_id}")
        return FixtureDetail(fixture, self.fixtures.list_changes(fixture_id))
