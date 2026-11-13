"""Analytics modüllerinin ortak tipleri. DB, ORM veya HTTP bilmez."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.core.enums import MatchResult

FORM_LENGTH = 5


@dataclass(frozen=True)
class PointsTable:
    """Sonuç başına puan. Değerler lig kurallarından (rules spec) gelir."""

    win: int
    draw: int
    loss: int

    def for_result(self, result: MatchResult) -> int:
        return {MatchResult.WIN: self.win, MatchResult.DRAW: self.draw}.get(result, self.loss)


class RoundLike(Protocol):
    @property
    def round(self) -> str | None: ...


def in_rounds[M: RoundLike](matches: Iterable[M], round_pattern: str | None) -> list[M]:
    """Lig kuralındaki haftalara (ör. `^Regular Season`) giren maçlar; desen yoksa hepsi.

    Puan tablosu, sezon özeti ve takım analizi aynı maç kümesini kullansın diye tek yerde.
    """
    if not round_pattern:
        return list(matches)
    pattern = re.compile(round_pattern)
    return [m for m in matches if pattern.search(m.round or "")]


class MatchLike(Protocol):
    """Hesaplamaların ihtiyaç duyduğu minimum maç bilgisi. ORM Fixture modeli de bunu karşılar."""

    @property
    def home_team_id(self) -> int: ...
    @property
    def away_team_id(self) -> int: ...
    @property
    def home_goals(self) -> int | None: ...
    @property
    def away_goals(self) -> int | None: ...
    @property
    def kickoff_at(self) -> datetime: ...
    @property
    def round(self) -> str | None: ...


def is_scored(match: MatchLike) -> bool:
    return match.home_goals is not None and match.away_goals is not None


def scored_in_order(matches: Iterable[MatchLike]) -> list[MatchLike]:
    """Skoru olan maçlar, oynanma sırasına göre. Skorsuz kayıtlar hesaba katılmaz."""
    return sorted((m for m in matches if is_scored(m)), key=lambda m: m.kickoff_at)


def goals_for_team(match: MatchLike, team_id: int) -> tuple[int, int]:
    """(attığı, yediği) — maç skorlu olmalı."""
    assert match.home_goals is not None and match.away_goals is not None
    if team_id == match.home_team_id:
        return match.home_goals, match.away_goals
    if team_id == match.away_team_id:
        return match.away_goals, match.home_goals
    raise ValueError(f"takım {team_id} bu maçta oynamadı")


def result_for(match: MatchLike, team_id: int) -> MatchResult:
    scored, conceded = goals_for_team(match, team_id)
    if scored > conceded:
        return MatchResult.WIN
    if scored < conceded:
        return MatchResult.LOSS
    return MatchResult.DRAW
