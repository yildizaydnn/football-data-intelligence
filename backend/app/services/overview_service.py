from dataclasses import dataclass
from datetime import UTC, datetime

from app.analytics.season_summary import SeasonSummary, summarize_season
from app.core.enums import MatchStatus
from app.models import Fixture, League, Season, SyncRun
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.sync_repository import SyncRunRepository
from app.services.league_service import LeagueService
from app.services.standings_service import StandingEntry, StandingsService

TOP_TEAMS = 5
RECENT_RESULTS = 5
UPCOMING_MATCHES = 5


@dataclass(frozen=True)
class Overview:
    league: League
    season: Season
    summary: SeasonSummary
    top_teams: list[StandingEntry]
    recent_results: list[Fixture]
    upcoming: list[Fixture]
    live: list[Fixture]
    last_sync: SyncRun | None


class OverviewService:
    """Dashboard ekranı için tek çağrıda sezon özeti."""

    def __init__(
        self,
        fixtures: FixtureRepository,
        sync_runs: SyncRunRepository,
        leagues: LeagueService,
        standings: StandingsService,
    ) -> None:
        self.fixtures = fixtures
        self.sync_runs = sync_runs
        self.leagues = leagues
        self.standings = standings

    def get_overview(
        self, league_id: int, season_year: int | None = None, *, now: datetime | None = None
    ) -> Overview:
        league = self.leagues.get_league(league_id)
        season = self.leagues.resolve_season(league_id, season_year)
        all_fixtures, _ = self.fixtures.list_filtered(season.id)

        return Overview(
            league=league,
            season=season,
            summary=summarize_season(all_fixtures),
            top_teams=self.standings.get_standings(league_id, season.year).entries[:TOP_TEAMS],
            recent_results=self.fixtures.list_recent_results(season.id, RECENT_RESULTS),
            upcoming=self.fixtures.list_upcoming(
                season.id, now or datetime.now(UTC), UPCOMING_MATCHES
            ),
            live=[f for f in all_fixtures if f.status is MatchStatus.LIVE],
            last_sync=self.sync_runs.latest(),
        )
