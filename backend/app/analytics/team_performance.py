"""Takım performans metrikleri (saf fonksiyon): form, oranlar, ortalamalar, iç saha/deplasman."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from app.analytics.common import (
    FORM_LENGTH,
    MatchLike,
    PointsTable,
    goals_for_team,
    result_for,
    scored_in_order,
)
from app.core.enums import MatchResult


@dataclass
class SplitStats:
    """Bir maç grubu (tümü / iç saha / deplasman) için toplamlar ve türetilmiş oranlar."""

    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    clean_sheets: int = 0
    failed_to_score: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def win_rate(self) -> float:
        return _ratio(self.won, self.played)

    @property
    def draw_rate(self) -> float:
        return _ratio(self.drawn, self.played)

    @property
    def loss_rate(self) -> float:
        return _ratio(self.lost, self.played)

    @property
    def avg_goals_for(self) -> float:
        return _ratio(self.goals_for, self.played)

    @property
    def avg_goals_against(self) -> float:
        return _ratio(self.goals_against, self.played)

    @property
    def points_per_game(self) -> float:
        return _ratio(self.points, self.played)

    def record(self, scored: int, conceded: int, result: MatchResult, points: int) -> None:
        self.played += 1
        self.points += points
        self.goals_for += scored
        self.goals_against += conceded
        self.clean_sheets += conceded == 0
        self.failed_to_score += scored == 0
        if result is MatchResult.WIN:
            self.won += 1
        elif result is MatchResult.DRAW:
            self.drawn += 1
        else:
            self.lost += 1


@dataclass(frozen=True)
class TimelinePoint:
    """Grafik için maç maç ilerleme."""

    kickoff_at: datetime
    opponent_id: int
    is_home: bool
    goals_for: int
    goals_against: int
    result: MatchResult
    cumulative_points: int


@dataclass
class TeamPerformance:
    team_id: int
    overall: SplitStats = field(default_factory=SplitStats)
    home: SplitStats = field(default_factory=SplitStats)
    away: SplitStats = field(default_factory=SplitStats)
    form: list[MatchResult] = field(default_factory=list)  # son N maç, eskiden yeniye
    timeline: list[TimelinePoint] = field(default_factory=list)

    @property
    def current_streak(self) -> tuple[MatchResult, int] | None:
        """Devam eden seri, ör. (WIN, 3). Hiç maç yoksa None."""
        if not self.timeline:
            return None
        last = self.timeline[-1].result
        count = 0
        for point in reversed(self.timeline):
            if point.result is not last:
                break
            count += 1
        return last, count


def calculate_team_performance(
    team_id: int, matches: Iterable[MatchLike], points: PointsTable
) -> TeamPerformance:
    """Takımın oynadığı skorlu maçlardan performans özeti. Takımın oynamadığı maçlar yok sayılır."""
    perf = TeamPerformance(team_id)
    cumulative = 0

    for match in scored_in_order(matches):
        is_home = match.home_team_id == team_id
        if not is_home and match.away_team_id != team_id:
            continue
        scored, conceded = goals_for_team(match, team_id)
        result = result_for(match, team_id)
        earned = points.for_result(result)
        cumulative += earned

        perf.overall.record(scored, conceded, result, earned)
        (perf.home if is_home else perf.away).record(scored, conceded, result, earned)
        perf.timeline.append(
            TimelinePoint(
                kickoff_at=match.kickoff_at,
                opponent_id=match.away_team_id if is_home else match.home_team_id,
                is_home=is_home,
                goals_for=scored,
                goals_against=conceded,
                result=result,
                cumulative_points=cumulative,
            )
        )

    perf.form = [p.result for p in perf.timeline[-FORM_LENGTH:]]
    return perf


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0
