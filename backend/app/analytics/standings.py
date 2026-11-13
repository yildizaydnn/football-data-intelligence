"""Puan tablosu hesaplayıcı (saf fonksiyon).

Lige özel her şey `StandingsRules` ile dışarıdan gelir (rules spec katmanı çözer):
puan değerleri, sıralama kriterleri, tabloya giren haftalar ve puan silme cezaları.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from app.analytics.common import (
    FORM_LENGTH,
    MatchLike,
    PointsTable,
    goals_for_team,
    in_rounds,
    result_for,
    scored_in_order,
)
from app.analytics.tiebreakers import HeadToHeadOptions, RankingContext, rank
from app.core.enums import MatchResult


@dataclass(frozen=True)
class StandingsRules:
    points: PointsTable
    tiebreakers: tuple[str, ...]
    head_to_head: HeadToHeadOptions = field(default_factory=HeadToHeadOptions)
    round_pattern: str | None = None  # regex; yalnızca eşleşen haftalar tabloya girer
    deductions: Mapping[int, int] = field(default_factory=dict)  # iç team_id → silinen puan


@dataclass
class StandingRow:
    team_id: int
    position: int = 0
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    earned_points: int = 0
    deduction: int = 0
    form: list[MatchResult] = field(default_factory=list)  # son N maç, eskiden yeniye

    @property
    def points(self) -> int:
        return self.earned_points - self.deduction

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def record(self, scored: int, conceded: int, result: MatchResult, points: PointsTable) -> None:
        self.played += 1
        self.goals_for += scored
        self.goals_against += conceded
        self.earned_points += points.for_result(result)
        if result is MatchResult.WIN:
            self.won += 1
        elif result is MatchResult.DRAW:
            self.drawn += 1
        else:
            self.lost += 1
        self.form = [*self.form, result][-FORM_LENGTH:]


def calculate_standings(
    matches: Iterable[MatchLike], rules: StandingsRules, team_ids: Iterable[int] = ()
) -> list[StandingRow]:
    """Bitmiş maçlardan puan tablosu üretir.

    `team_ids` verilirse henüz maç oynamamış takımlar da tabloda 0 puanla yer alır.
    """
    counted = in_rounds(scored_in_order(matches), rules.round_pattern)

    rows: dict[int, StandingRow] = {team_id: StandingRow(team_id) for team_id in team_ids}
    for match in counted:
        for team_id in (match.home_team_id, match.away_team_id):
            row = rows.setdefault(team_id, StandingRow(team_id))
            row.record(*goals_for_team(match, team_id), result_for(match, team_id), rules.points)
    for team_id, deduction in rules.deductions.items():
        if team_id in rows:
            rows[team_id].deduction = deduction

    context = RankingContext(rows, counted, rules.points, rules.head_to_head)
    ordered = [rows[team_id] for team_id in rank(list(rows), rules.tiebreakers, context)]
    for position, row in enumerate(ordered, start=1):
        row.position = position
    return ordered
