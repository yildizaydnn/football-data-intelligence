from app.core.enums import MatchStatus
from app.schemas.common import Schema
from app.schemas.fixture import FixtureOut
from app.schemas.league import LeagueOut, SeasonOut
from app.schemas.standings import StandingRowOut
from app.schemas.sync import SyncRunOut
from app.services.overview_service import Overview


class RoundGoalsOut(Schema):
    round: str
    number: int | None
    matches: int
    goals: int


class SeasonSummaryOut(Schema):
    total_matches: int
    by_status: dict[MatchStatus, int]
    finished: int
    total_goals: int
    avg_goals_per_match: float
    home_wins: int
    draws: int
    away_wins: int
    home_win_rate: float
    draw_rate: float
    away_win_rate: float
    goals_by_round: list[RoundGoalsOut]
    current_round: RoundGoalsOut | None


class OverviewOut(Schema):
    league: LeagueOut
    season: SeasonOut
    summary: SeasonSummaryOut
    top_teams: list[StandingRowOut]
    recent_results: list[FixtureOut]
    upcoming: list[FixtureOut]
    live: list[FixtureOut]
    last_sync: SyncRunOut | None

    @classmethod
    def from_overview(cls, overview: Overview) -> "OverviewOut":
        return cls(
            league=LeagueOut.model_validate(overview.league),
            season=SeasonOut.model_validate(overview.season),
            summary=SeasonSummaryOut.model_validate(overview.summary),
            top_teams=[StandingRowOut.from_entry(e) for e in overview.top_teams],
            recent_results=[FixtureOut.model_validate(f) for f in overview.recent_results],
            upcoming=[FixtureOut.model_validate(f) for f in overview.upcoming],
            live=[FixtureOut.model_validate(f) for f in overview.live],
            last_sync=SyncRunOut.model_validate(overview.last_sync) if overview.last_sync else None,
        )
