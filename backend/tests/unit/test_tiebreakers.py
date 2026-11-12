"""Sıralama kriterlerinin lig kuralına göre farklı tablo üretmesi (saf, DB'siz)."""

from app.analytics.standings import calculate_standings
from app.analytics.tiebreakers import HeadToHeadOptions
from tests.rules_helpers import standings_rules
from tests.unit.analytics_helpers import match

A, B, C, D, E = 1, 2, 3, 4, 5

# A ve B 7 puanda eşit. A ikili maçlarda üstün (4-1 puan), B genel averajda üstün.
SEASON = [
    match(A, B, "1-0", week=1),
    match(B, A, "0-0", week=2),
    match(B, C, "5-0", week=3),
    match(C, B, "0-5", week=4),
    match(A, C, "1-0", week=5),
    match(C, A, "1-0", week=6),
]


def _order(rows) -> list[int]:
    return [r.team_id for r in rows]


def test_same_matches_different_league_rules() -> None:
    h2h_first = standings_rules(round_pattern=None)  # Süper Lig spec'i
    overall_first = standings_rules(
        None,
        tiebreakers=("points", "goal_difference", "goals_for", "h2h_points"),
        round_pattern=None,
    )

    assert _order(calculate_standings(SEASON, h2h_first))[:2] == [A, B]
    assert _order(calculate_standings(SEASON, overall_first))[:2] == [B, A]


def test_point_deduction_changes_order() -> None:
    rules = standings_rules(round_pattern=None, deductions={A: 3})

    rows = calculate_standings(SEASON, rules)

    a = next(r for r in rows if r.team_id == A)
    assert (a.earned_points, a.deduction, a.points) == (7, 3, 4)
    assert _order(rows)[0] == B


def test_round_filter_excludes_playoff_matches() -> None:
    playoff = match(C, A, "3-0", week=7, round="Relegation Round")
    regular = [
        match(
            m.home_team_id,
            m.away_team_id,
            f"{m.home_goals}-{m.away_goals}",
            week=i,
            round=f"Regular Season - {i}",
        )
        for i, m in enumerate(SEASON, start=1)
    ]
    rules = standings_rules()  # spec: include_rounds "^Regular Season"

    rows = {r.team_id: r for r in calculate_standings([*regular, playoff], rules)}

    assert rows[C].played == 4  # play-off maçı sayılmadı


def test_reapply_head_to_head_to_subgroups() -> None:
    # A, B, C 12'şer puan. Mini lig puanı: A 12, B 3, C 3 → A önde; B ile C eşit.
    # B-C'yi ayıran ikili averaj:
    #  - üçlü grup kapsamı: B -4, C -3 → C önde
    #  - alt gruba yeniden uygulama (sadece B-C maçları): B +1, C -1 → B önde
    matches = [
        match(A, B, "1-0", week=1), match(B, A, "0-4", week=2),
        match(A, C, "1-0", week=3), match(C, A, "0-1", week=4),
        match(B, C, "2-0", week=5), match(C, B, "1-0", week=6),
        match(B, D, "1-0", week=7), match(D, B, "0-1", week=8), match(B, E, "1-0", week=9),
        match(C, D, "1-0", week=10), match(D, C, "0-1", week=11), match(C, E, "1-0", week=12),
        match(D, A, "1-0", week=13), match(E, A, "1-0", week=14),
    ]  # fmt: skip
    criteria = ("points", "h2h_points", "h2h_goal_difference")
    whole = standings_rules(None, tiebreakers=criteria, round_pattern=None)
    reapply = standings_rules(
        None,
        tiebreakers=criteria,
        round_pattern=None,
        head_to_head=HeadToHeadOptions(reapply_to_subgroups=True),
    )

    rows = calculate_standings(matches, whole)
    assert [r.points for r in rows[:3]] == [12, 12, 12]
    assert _order(rows)[:3] == [A, C, B]
    assert _order(calculate_standings(matches, reapply))[:3] == [A, B, C]


def test_goals_against_and_away_goals_criteria() -> None:
    matches = [match(A, C, "2-1", week=1), match(D, B, "1-2", week=2)]  # A ve B: 3 puan, +1, 2 gol
    away_first = standings_rules(
        None,
        tiebreakers=("points", "goal_difference", "goals_for", "away_goals_for"),
        round_pattern=None,
    )
    fewest_conceded = standings_rules(
        None, tiebreakers=("points", "goals_against"), round_pattern=None
    )

    assert _order(calculate_standings(matches, away_first))[:2] == [B, A]
    assert _order(calculate_standings(matches, fewest_conceded))[:2] == [A, B]  # eşit → team_id
