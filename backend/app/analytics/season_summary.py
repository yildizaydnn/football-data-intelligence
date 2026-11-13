"""Sezon geneli özet istatistikler (saf fonksiyon)."""

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from app.analytics.common import MatchLike, in_rounds, scored_in_order
from app.core.enums import MatchStatus


class StatusMatchLike(MatchLike, Protocol):
    @property
    def status(self) -> MatchStatus: ...
    @property
    def round(self) -> str | None: ...


@dataclass(frozen=True)
class RoundGoals:
    round: str  # API'deki ham değer, ör. "Regular Season - 6"
    number: int | None  # sondaki hafta numarası (6); çıkarılamazsa None
    matches: int
    goals: int


@dataclass
class SeasonSummary:
    total_matches: int = 0
    by_status: dict[MatchStatus, int] = field(default_factory=dict)
    total_goals: int = 0
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0
    goals_by_round: list[RoundGoals] = field(default_factory=list)  # hafta sırasına göre

    @property
    def current_round(self) -> RoundGoals | None:
        """Bitmiş maçı olan en ileri hafta."""
        return self.goals_by_round[-1] if self.goals_by_round else None

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


def summarize_season(
    matches: Iterable[StatusMatchLike], round_pattern: str | None = None
) -> SeasonSummary:
    """Gol ve sonuç dağılımı yalnızca bitmiş maçlardan; canlı maçların anlık skoru sayılmaz.

    `round_pattern` (lig kuralından) verilirse yalnızca eşleşen haftalar sayılır; puan
    tablosuyla aynı kapsam (ör. küme düşme play-off'u özete girmez).
    """
    matches = in_rounds(matches, round_pattern)
    statuses = Counter(m.status for m in matches)
    summary = SeasonSummary(
        total_matches=len(matches),
        by_status={status: statuses.get(status, 0) for status in MatchStatus},
    )
    rounds: dict[str, list[int]] = {}  # round → [maç, gol]
    first_kickoff: dict[str, datetime] = {}
    for match in scored_in_order(m for m in matches if m.status is MatchStatus.FINISHED):
        assert match.home_goals is not None and match.away_goals is not None
        goals = match.home_goals + match.away_goals
        summary.total_goals += goals
        if match.round:
            stats = rounds.setdefault(match.round, [0, 0])
            stats[0] += 1
            stats[1] += goals
            first_kickoff.setdefault(match.round, match.kickoff_at)
        if match.home_goals > match.away_goals:
            summary.home_wins += 1
        elif match.home_goals < match.away_goals:
            summary.away_wins += 1
        else:
            summary.draws += 1

    # Hafta numarasına göre; numarasız (ör. play-off) haftalar ilk maç tarihine göre sona.
    def order(name: str) -> tuple[bool, int, datetime]:
        number = _round_number(name)
        return number is None, number or 0, first_kickoff[name]

    summary.goals_by_round = [
        RoundGoals(name, _round_number(name), *rounds[name]) for name in sorted(rounds, key=order)
    ]
    return summary


def _round_number(name: str) -> int | None:
    match = re.search(r"(\d+)\s*$", name)
    return int(match.group(1)) if match else None
