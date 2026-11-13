"""İki takımın karşılaştırması (saf): sezon performansları + kendi aralarındaki maçlar."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.analytics.common import MatchLike, PointsTable, goals_for_team, result_for, scored_in_order
from app.analytics.team_performance import TeamPerformance, calculate_team_performance
from app.core.enums import MatchResult


@dataclass(frozen=True)
class HeadToHeadMatch:
    kickoff_at: datetime
    home_team_id: int
    away_team_id: int
    home_goals: int
    away_goals: int


@dataclass(frozen=True)
class HeadToHeadRecord:
    matches: list[HeadToHeadMatch]
    team_a_wins: int
    draws: int
    team_b_wins: int
    team_a_goals: int
    team_b_goals: int


@dataclass(frozen=True)
class TeamComparison:
    team_a: TeamPerformance
    team_b: TeamPerformance
    head_to_head: HeadToHeadRecord


def compare_teams(
    team_a_id: int, team_b_id: int, matches: Iterable[MatchLike], points: PointsTable
) -> TeamComparison:
    matches = list(matches)
    mutual = [
        m
        for m in scored_in_order(matches)
        if {m.home_team_id, m.away_team_id} == {team_a_id, team_b_id}
    ]
    results = [result_for(m, team_a_id) for m in mutual]
    goals = [goals_for_team(m, team_a_id) for m in mutual]
    record = HeadToHeadRecord(
        matches=[
            HeadToHeadMatch(
                m.kickoff_at, m.home_team_id, m.away_team_id, m.home_goals, m.away_goals
            )  # type: ignore[arg-type]
            for m in mutual
        ],
        team_a_wins=results.count(MatchResult.WIN),
        draws=results.count(MatchResult.DRAW),
        team_b_wins=results.count(MatchResult.LOSS),
        team_a_goals=sum(g[0] for g in goals),
        team_b_goals=sum(g[1] for g in goals),
    )
    return TeamComparison(
        team_a=calculate_team_performance(team_a_id, matches, points),
        team_b=calculate_team_performance(team_b_id, matches, points),
        head_to_head=record,
    )
