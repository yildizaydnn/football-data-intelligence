"""Sezon geneli özet istatistikler (saf fonksiyon)."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol

from app.analytics.common import MatchLike, scored_in_order
from app.core.enums import MatchStatus


class StatusMatchLike(MatchLike, Protocol):
    @property
    def status(self) -> MatchStatus: ...


@dataclass
class SeasonSummary:
    total_matches: int = 0
    by_status: dict[MatchStatus, int] = field(default_factory=dict)
    total_goals: int = 0
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0

    @property
    def finished(self) -> int:
        return self.by_status.get(MatchStatus.FINISHED, 0)

    @property
    def avg_goals_per_match(self) -> float:
        return self.total_goals / self.finished if self.finished else 0.0

    @property
    def home_win_rate(self) -> float:
        return self.home_wins / self.finished if self.finished else 0.0

    @property
    def draw_rate(self) -> float:
        return self.draws / self.finished if self.finished else 0.0

    @property
    def away_win_rate(self) -> float:
        return self.away_wins / self.finished if self.finished else 0.0


def summarize_season(matches: Iterable[StatusMatchLike]) -> SeasonSummary:
    """Gol ve sonuç dağılımı yalnızca bitmiş maçlardan; canlı maçların anlık skoru sayılmaz."""
    matches = list(matches)
    statuses = Counter(m.status for m in matches)
    summary = SeasonSummary(
        total_matches=len(matches),
        by_status={status: statuses.get(status, 0) for status in MatchStatus},
    )
    for match in scored_in_order(m for m in matches if m.status is MatchStatus.FINISHED):
        assert match.home_goals is not None and match.away_goals is not None
        summary.total_goals += match.home_goals + match.away_goals
        if match.home_goals > match.away_goals:
            summary.home_wins += 1
        elif match.home_goals < match.away_goals:
            summary.away_wins += 1
        else:
            summary.draws += 1
    return summary
