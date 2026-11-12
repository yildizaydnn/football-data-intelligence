"""Puan tablosu sıralama kriterleri: isimlendirilmiş ve birleştirilebilir (saf fonksiyonlar).

Lig kuralları (rules spec) yalnızca kriter adlarını ve sırasını verir, ör.
    [points, h2h_points, h2h_goal_difference, goal_difference, goals_for]
Sıralama özyinelemelidir: ilk kriter takımları gruplara ayırır, hâlâ eşit kalan her gruba
bir sonraki kriter uygulanır. Tüm kriterler tükenirse team_id ile deterministik sıralanır.

İkili (h2h) kriterler, eşitliğe giren takımların kendi aralarındaki maçlardan oluşan mini
lig üzerinden hesaplanır. Kapsam: ilk h2h kriterine gelindiğindeki eşit grup; kural
`reapply_to_subgroups` ise (UEFA usulü) her alt grupta mini lig yeniden kurulur.
"""

from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from itertools import combinations
from typing import Protocol

from app.analytics.common import MatchLike, PointsTable, goals_for_team, result_for


class RowLike(Protocol):
    @property
    def points(self) -> int: ...
    @property
    def goal_difference(self) -> int: ...
    @property
    def goals_for(self) -> int: ...
    @property
    def goals_against(self) -> int: ...
    @property
    def won(self) -> int: ...


@dataclass(frozen=True)
class HeadToHeadOptions:
    requires_all_matches: bool = True  # tüm karşılıklı maçlar oynanmadan h2h uygulanmaz
    matches_per_pair: int = 2  # çift devreli lig
    reapply_to_subgroups: bool = False


@dataclass(frozen=True)
class RankingContext:
    rows: Mapping[int, RowLike]
    matches: Sequence[MatchLike]  # tabloya dahil, skorlu maçlar
    points: PointsTable
    h2h: HeadToHeadOptions = field(default_factory=HeadToHeadOptions)


@dataclass
class _MiniStats:
    points: int = 0
    goal_difference: int = 0
    goals_for: int = 0
    away_goals_for: int = 0


# Kriter: (sıralanacak grup, h2h kapsamı, bağlam) → takım başına değer (büyük olan önde)
Criterion = Callable[[Sequence[int], Sequence[int], RankingContext], Mapping[int, float]]


def _overall(attribute: str, sign: int = 1) -> Criterion:
    def criterion(group: Sequence[int], _scope: Sequence[int], ctx: RankingContext):
        return {team: sign * getattr(ctx.rows[team], attribute) for team in group}

    return criterion


def _away_goals_for(group: Sequence[int], _scope: Sequence[int], ctx: RankingContext):
    totals = dict.fromkeys(group, 0)
    for match in ctx.matches:
        if match.away_team_id in totals:
            totals[match.away_team_id] += match.away_goals or 0
    return totals


def _mini_league(scope: Sequence[int], ctx: RankingContext) -> dict[int, _MiniStats] | None:
    members = set(scope)
    mutual = [m for m in ctx.matches if m.home_team_id in members and m.away_team_id in members]
    if ctx.h2h.requires_all_matches:
        played = Counter(frozenset((m.home_team_id, m.away_team_id)) for m in mutual)
        if any(played[frozenset(p)] < ctx.h2h.matches_per_pair for p in combinations(scope, 2)):
            return None
    stats = {team: _MiniStats() for team in scope}
    for match in mutual:
        for team in (match.home_team_id, match.away_team_id):
            scored, conceded = goals_for_team(match, team)
            stats[team].points += ctx.points.for_result(result_for(match, team))
            stats[team].goal_difference += scored - conceded
            stats[team].goals_for += scored
            if team == match.away_team_id:
                stats[team].away_goals_for += scored
    return stats


def _h2h(metric: str) -> Criterion:
    def criterion(group: Sequence[int], scope: Sequence[int], ctx: RankingContext):
        stats = _mini_league(scope, ctx)
        if stats is None:  # uygulanamaz: grubu ayırmaz, sonraki kritere geçilir
            return dict.fromkeys(group, 0)
        return {team: getattr(stats[team], metric) for team in group}

    criterion.is_head_to_head = True  # type: ignore[attr-defined]
    return criterion


CRITERIA: dict[str, Criterion] = {
    "points": _overall("points"),
    "goal_difference": _overall("goal_difference"),
    "goals_for": _overall("goals_for"),
    "goals_against": _overall("goals_against", sign=-1),  # az yiyen önde
    "wins": _overall("won"),
    "away_goals_for": _away_goals_for,
    "h2h_points": _h2h("points"),
    "h2h_goal_difference": _h2h("goal_difference"),
    "h2h_goals_for": _h2h("goals_for"),
    "h2h_away_goals_for": _h2h("away_goals_for"),
}


def rank(teams: Sequence[int], criteria: Sequence[str], ctx: RankingContext) -> list[int]:
    """Takımları kriter sırasına göre dizer. Bilinmeyen kriter adı KeyError verir."""
    functions = [CRITERIA[name] for name in criteria]

    def split(group: list[int], index: int, scope: list[int] | None) -> list[int]:
        if len(group) <= 1 or index == len(functions):
            return sorted(group)
        criterion = functions[index]
        is_h2h = getattr(criterion, "is_head_to_head", False)
        h2h_scope = group if is_h2h and (scope is None or ctx.h2h.reapply_to_subgroups) else scope
        values = criterion(group, h2h_scope or group, ctx)
        ordered: list[int] = []
        for value in sorted(set(values.values()), reverse=True):
            tied = [team for team in group if values[team] == value]
            ordered += split(tied, index + 1, h2h_scope)
        return ordered

    return split(list(teams), 0, None)
