from dataclasses import dataclass

from app.analytics.common import in_rounds
from app.analytics.team_performance import TeamPerformance, calculate_team_performance
from app.core.exceptions import NotFoundError
from app.models import Season, Team
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.team_repository import TeamRepository
from app.rules.engine import RuleEngine
from app.services.league_service import LeagueService


@dataclass(frozen=True)
class TeamStats:
    season: Season
    team: Team
    performance: TeamPerformance
    opponents: dict[int, Team]  # timeline'daki opponent_id → Team


class TeamStatsService:
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

    def list_teams(self, league_id: int, season_year: int | None = None) -> list[Team]:
        """Sezonun takımları: puan tablosundakilerle aynı (ör. yalnızca play-off'a çıkan
        alt lig takımı dahil değil)."""
        league = self.leagues.get_league(league_id)
        season = self.leagues.resolve_season(league_id, season_year)
        rounds = self.rules.resolve(league.external_id, season.year).standings.include_rounds
        return self.teams.list_by_season(season.id, rounds)

    def get_team(self, team_id: int) -> Team:
        team = self.teams.get(team_id)
        if team is None:
            raise NotFoundError(f"Takım bulunamadı: {team_id}")
        return team

    def get_team_stats(
        self, league_id: int, team_id: int, season_year: int | None = None
    ) -> TeamStats:
        league = self.leagues.get_league(league_id)
        season = self.leagues.resolve_season(league_id, season_year)
        team = self.get_team(team_id)
        context = self.rules.resolve(league.external_id, season.year)
        rounds = context.standings.include_rounds
        if team_id not in {t.id for t in self.teams.list_by_season(season.id, rounds)}:
            raise NotFoundError(f"{team.name} bu lig ve sezonda yer almıyor")
        # Puan tablosuyla aynı maçlar: kural dışındaki turlar (ör. küme play-off'u) sayılmaz.
        matches = in_rounds(self.fixtures.list_finished(season.id, team_id=team_id), rounds)
        performance = calculate_team_performance(team_id, matches, context.points_table)

        opponent_ids = {p.opponent_id for p in performance.timeline}
        opponents = {t.id: t for t in self.teams.list_by_ids(opponent_ids)}
        return TeamStats(season, team, performance, opponents)
