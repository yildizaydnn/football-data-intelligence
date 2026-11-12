"""Puan tablosu hesaplayıcı (saf fonksiyon).

Sıralama (Süper Lig usulü):
  1. puan
  2. ikili puan   → eşit puanlı takımların kendi aralarındaki maçlarda aldığı puan
  3. ikili averaj → aynı maçlardaki gol farkı
  4. genel averaj → atılan gol → galibiyet sayısı → team_id (deterministik olsun diye)

İkili kriterler, eşit puanlı takımlar birbirleriyle tüm maçlarını (iç saha + deplasman)
oynamışsa uygulanır; aksi halde o grup için doğrudan genel averaja geçilir.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from itertools import combinations

from app.analytics.common import (
    FORM_LENGTH,
    POINTS,
    MatchLike,
    goals_for_team,
    result_for,
    scored_in_order,
)
from app.core.enums import MatchResult

MATCHES_PER_PAIR = 2  # çift devreli lig: her ikili bir iç saha, bir deplasman maçı oynar


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
    points: int = 0
    form: list[MatchResult] = field(default_factory=list)  # son N maç, eskiden yeniye

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def record(self, scored: int, conceded: int, result: MatchResult) -> None:
        self.played += 1
        self.goals_for += scored
        self.goals_against += conceded
        self.points += POINTS[result]
        if result is MatchResult.WIN:
            self.won += 1
        elif result is MatchResult.DRAW:
            self.drawn += 1
        else:
            self.lost += 1
        self.form = [*self.form, result][-FORM_LENGTH:]


def calculate_standings(
    matches: Iterable[MatchLike], team_ids: Iterable[int] = ()
) -> list[StandingRow]:
    """Bitmiş maçlardan puan tablosu üretir.

    `team_ids` verilirse henüz maç oynamamış takımlar da tabloda 0 puanla yer alır.
    """
    rows: dict[int, StandingRow] = {team_id: StandingRow(team_id) for team_id in team_ids}
    scored = scored_in_order(matches)

    for match in scored:
        for team_id in (match.home_team_id, match.away_team_id):
            row = rows.setdefault(team_id, StandingRow(team_id))
            row.record(*goals_for_team(match, team_id), result_for(match, team_id))

    tied_groups: defaultdict[int, set[int]] = defaultdict(set)
    for row in rows.values():
        tied_groups[row.points].add(row.team_id)
    h2h: dict[int, tuple[int, int]] = {}
    for group in tied_groups.values():
        if len(group) > 1:
            h2h |= _head_to_head(group, scored)

    def sort_key(r: StandingRow) -> tuple[int, ...]:
        h2h_points, h2h_gd = h2h.get(r.team_id, (0, 0))
        overall = (-r.goal_difference, -r.goals_for, -r.won, r.team_id)
        return (-r.points, -h2h_points, -h2h_gd, *overall)

    ordered = sorted(rows.values(), key=sort_key)
    for position, row in enumerate(ordered, start=1):
        row.position = position
    return ordered


def _head_to_head(group: set[int], matches: Sequence[MatchLike]) -> dict[int, tuple[int, int]]:
    """Eşit puanlı takımlar arasındaki mini lig: takım → (ikili puan, ikili averaj).

    Gruptaki her ikili tüm maçlarını oynamadıysa boş döner (ikili kriter uygulanmaz).
    """
    mutual = [m for m in matches if m.home_team_id in group and m.away_team_id in group]
    played = Counter(frozenset((m.home_team_id, m.away_team_id)) for m in mutual)
    if any(played[frozenset(pair)] < MATCHES_PER_PAIR for pair in combinations(group, 2)):
        return {}

    stats = {team_id: [0, 0] for team_id in group}
    for match in mutual:
        for team_id in (match.home_team_id, match.away_team_id):
            scored, conceded = goals_for_team(match, team_id)
            stats[team_id][0] += POINTS[result_for(match, team_id)]
            stats[team_id][1] += scored - conceded
    return {team_id: (points, gd) for team_id, (points, gd) in stats.items()}
