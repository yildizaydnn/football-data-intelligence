from datetime import datetime

from pydantic import BaseModel

from app.analytics.team_performance import TeamPerformance
from app.core.enums import MatchResult
from app.schemas.common import Schema
from app.schemas.team import TeamRef
from app.services.insight_service import AiStatus, Insight


class InsightRequest(BaseModel):
    team_a_id: int
    team_b_id: int
    season: int | None = None


class TeamFactsOut(Schema):
    """Analizin dayandığı sayılar; arayüz metnin yanında gösterir (karşılaştırılabilir olsun)."""

    played: int
    points: int
    win_rate: float
    avg_goals_for: float
    avg_goals_against: float
    clean_sheets: int
    form: list[MatchResult]
    home_points: int
    away_points: int

    @classmethod
    def from_performance(cls, perf: TeamPerformance) -> "TeamFactsOut":
        o = perf.overall
        return cls(
            played=o.played,
            points=o.points,
            win_rate=o.win_rate,
            avg_goals_for=o.avg_goals_for,
            avg_goals_against=o.avg_goals_against,
            clean_sheets=o.clean_sheets,
            form=perf.form,
            home_points=perf.home.points,
            away_points=perf.away.points,
        )


class HeadToHeadOut(Schema):
    matches: int
    team_a_wins: int
    draws: int
    team_b_wins: int
    team_a_goals: int
    team_b_goals: int


class InsightOut(Schema):
    season: int
    team_a: TeamRef
    team_b: TeamRef
    team_a_facts: TeamFactsOut
    team_b_facts: TeamFactsOut
    head_to_head: HeadToHeadOut
    content: str
    model: str
    generated_at: datetime
    cached: bool  # true: önbellekten (LLM'e gidilmedi)
    unverified_numbers: list[str]  # metinde olup veride bulunamayan sayılar

    @classmethod
    def from_insight(cls, insight: Insight) -> "InsightOut":
        h2h = insight.comparison.head_to_head
        return cls(
            season=insight.season.year,
            team_a=TeamRef.model_validate(insight.team_a),
            team_b=TeamRef.model_validate(insight.team_b),
            team_a_facts=TeamFactsOut.from_performance(insight.comparison.team_a),
            team_b_facts=TeamFactsOut.from_performance(insight.comparison.team_b),
            head_to_head=HeadToHeadOut(
                matches=len(h2h.matches),
                team_a_wins=h2h.team_a_wins,
                draws=h2h.draws,
                team_b_wins=h2h.team_b_wins,
                team_a_goals=h2h.team_a_goals,
                team_b_goals=h2h.team_b_goals,
            ),
            content=insight.content,
            model=insight.model,
            generated_at=insight.generated_at,
            cached=insight.cached,
            unverified_numbers=insight.unverified_numbers,
        )


class AiStatusOut(Schema):
    enabled: bool
    daily_limit: int
    generated_today: int

    @classmethod
    def from_status(cls, status: AiStatus) -> "AiStatusOut":
        return cls(
            enabled=status.enabled,
            daily_limit=status.daily_limit,
            generated_today=status.generated_today,
        )
