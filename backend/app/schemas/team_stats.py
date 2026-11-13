from datetime import datetime

from pydantic import Field

from app.core.enums import MatchResult
from app.schemas.common import Schema
from app.schemas.team import TeamOut, TeamRef
from app.services.team_stats_service import TeamStats


class SplitStatsOut(Schema):
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    clean_sheets: int
    failed_to_score: int
    win_rate: float
    draw_rate: float
    loss_rate: float
    avg_goals_for: float
    avg_goals_against: float
    points_per_game: float


class TimelinePointOut(Schema):
    kickoff_at: datetime
    opponent: TeamRef
    is_home: bool
    goals_for: int
    goals_against: int
    result: MatchResult
    cumulative_points: int


class StreakOut(Schema):
    result: MatchResult
    count: int


class TeamStatsOut(Schema):
    season: int
    team: TeamOut
    overall: SplitStatsOut
    home: SplitStatsOut
    away: SplitStatsOut
    recent: SplitStatsOut = Field(description="Son 5 maç (form ile aynı pencere)")
    form: list[MatchResult]
    current_streak: StreakOut | None
    timeline: list[TimelinePointOut]

    @classmethod
    def from_stats(cls, stats: TeamStats) -> "TeamStatsOut":
        perf = stats.performance
        streak = perf.current_streak
        return cls(
            season=stats.season.year,
            team=TeamOut.model_validate(stats.team),
            overall=SplitStatsOut.model_validate(perf.overall),
            home=SplitStatsOut.model_validate(perf.home),
            away=SplitStatsOut.model_validate(perf.away),
            recent=SplitStatsOut.model_validate(perf.recent),
            form=perf.form,
            current_streak=StreakOut(result=streak[0], count=streak[1]) if streak else None,
            timeline=[
                TimelinePointOut(
                    kickoff_at=p.kickoff_at,
                    opponent=TeamRef.model_validate(stats.opponents[p.opponent_id]),
                    is_home=p.is_home,
                    goals_for=p.goals_for,
                    goals_against=p.goals_against,
                    result=p.result,
                    cumulative_points=p.cumulative_points,
                )
                for p in perf.timeline
            ],
        )
