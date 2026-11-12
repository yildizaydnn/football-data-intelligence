from dataclasses import dataclass

from app.analytics.standings import StandingRow, calculate_standings
from app.models import Season, Team
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.team_repository import TeamRepository
from app.rules.engine import RuleEngine
from app.rules.models import RuleContext
from app.services.league_service import LeagueService


@dataclass(frozen=True)
class StandingEntry:
    row: StandingRow
    team: Team


@dataclass(frozen=True)
class Standings:
    season: Season
    entries: list[StandingEntry]
    rules: RuleContext  # tabloyu üreten kurallar (bölgeler, sıralama kriterleri)


class StandingsService:
    """Repository'den maçları alır, analytics'e verir; tabloyu takım bilgisiyle birleştirir."""

    def __init__(
        self,
        fixtures: FixtureRepository,
        teams: TeamRepository,
        leagues: LeagueService,
        rules: RuleEngine,
    ) -> None:
        self.fixtures = fixtures
        self.teams = teams
        self.leagues = leagues
        self.rules = rules

    def get_standings(self, league_id: int, season_year: int | None = None) -> Standings:
        league = self.leagues.get_league(league_id)
        season = self.leagues.resolve_season(league_id, season_year)
        context = self.rules.resolve(league.external_id, season.year)
        # Tabloya yalnızca kuraldaki haftalarda (ör. normal sezon) oynayan takımlar girer.
        teams = {
            t.id: t for t in self.teams.list_by_season(season.id, context.standings.include_rounds)
        }
        rules = context.standings_rules({t.external_id: t.id for t in teams.values()})
        rows = calculate_standings(self.fixtures.list_finished(season.id), rules, team_ids=teams)
        entries = [StandingEntry(row, teams[row.team_id]) for row in rows]
        return Standings(season, entries, context)
