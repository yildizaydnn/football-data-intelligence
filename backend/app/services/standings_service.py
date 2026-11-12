from dataclasses import dataclass

from app.analytics.standings import StandingRow, calculate_standings
from app.models import Season, Team
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.team_repository import TeamRepository
from app.services.league_service import LeagueService


@dataclass(frozen=True)
class StandingEntry:
    row: StandingRow
    team: Team


@dataclass(frozen=True)
class Standings:
    season: Season
    entries: list[StandingEntry]


class StandingsService:
    """Repository'den maçları alır, analytics'e verir; tabloyu takım bilgisiyle birleştirir."""

    def __init__(
        self, fixtures: FixtureRepository, teams: TeamRepository, leagues: LeagueService
    ) -> None:
        self.fixtures = fixtures
        self.teams = teams
        self.leagues = leagues

    def get_standings(self, league_id: int, season_year: int | None = None) -> Standings:
        season = self.leagues.resolve_season(league_id, season_year)
        teams = {t.id: t for t in self.teams.list_by_season(season.id)}
        rows = calculate_standings(self.fixtures.list_finished(season.id), team_ids=teams)
        return Standings(season, [StandingEntry(row, teams[row.team_id]) for row in rows])
