from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

BASE = datetime(2024, 8, 10, 17, 0, tzinfo=UTC)


@dataclass(frozen=True)
class Match:
    """analytics.common.MatchLike'ı karşılayan basit test maçı."""

    home_team_id: int
    away_team_id: int
    home_goals: int | None
    away_goals: int | None
    kickoff_at: datetime


def match(home: int, away: int, score: str | None, week: int) -> Match:
    """match(1, 2, "2-1", week=1) → 1. haftada 1 evinde 2'yi 2-1 yendi."""
    if score is None:
        return Match(home, away, None, None, BASE + timedelta(weeks=week))
    home_goals, away_goals = (int(g) for g in score.split("-"))
    return Match(home, away, home_goals, away_goals, BASE + timedelta(weeks=week))
