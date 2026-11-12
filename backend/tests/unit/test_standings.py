from app.analytics.standings import calculate_standings as _calculate
from app.core.enums import MatchResult
from tests.rules_helpers import standings_rules
from tests.unit.analytics_helpers import match

# Test maçlarının "round" bilgisi yok; hafta filtresi kapatılır.
RULES = standings_rules(round_pattern=None)


def calculate_standings(matches, team_ids=()):
    return _calculate(matches, RULES, team_ids)


W, D, L = MatchResult.WIN, MatchResult.DRAW, MatchResult.LOSS
GS, FB, BJK, TS = 1, 2, 3, 4


def _table(rows):
    return {r.team_id: r for r in rows}


def test_points_goals_and_record() -> None:
    rows = _table(
        calculate_standings(
            [
                match(GS, FB, "2-1", week=1),
                match(BJK, GS, "0-0", week=2),
                match(FB, BJK, "3-0", week=3),
            ]
        )
    )

    gs = rows[GS]
    assert (gs.played, gs.won, gs.drawn, gs.lost, gs.points) == (2, 1, 1, 0, 4)
    assert (gs.goals_for, gs.goals_against, gs.goal_difference) == (2, 1, 1)
    fb = rows[FB]
    assert (fb.played, fb.won, fb.lost, fb.points, fb.goal_difference) == (2, 1, 1, 3, 2)


def test_order_by_points_then_goal_difference_then_goals_for() -> None:
    rows = calculate_standings(
        [
            match(GS, TS, "1-0", week=1),  # GS: 3 puan, +1
            match(FB, TS, "3-0", week=2),  # FB: 3 puan, +3
            match(BJK, TS, "4-1", week=3),  # BJK: 3 puan, +3, 4 gol
        ]
    )

    assert [r.team_id for r in rows] == [BJK, FB, GS, TS]
    assert [r.position for r in rows] == [1, 2, 3, 4]


def test_full_tie_is_deterministic() -> None:
    rows = calculate_standings([match(FB, GS, "1-1", week=1)])

    assert [r.team_id for r in rows] == [GS, FB]


def test_unscored_matches_are_ignored() -> None:
    rows = _table(calculate_standings([match(GS, FB, "1-0", week=1), match(FB, GS, None, week=2)]))

    assert rows[GS].played == 1
    assert rows[FB].played == 1


def test_teams_without_matches_are_included_when_given() -> None:
    rows = calculate_standings([match(GS, FB, "1-0", week=1)], team_ids=[GS, FB, BJK])

    # BJK maç oynamadı (averaj 0), FB kaybetti (averaj -1) → BJK üstte
    assert [r.team_id for r in rows] == [GS, BJK, FB]
    assert (rows[1].played, rows[1].points, rows[1].form) == (0, 0, [])


def test_form_is_last_five_in_chronological_order_regardless_of_input_order() -> None:
    results = ["1-0", "0-1", "1-1", "2-0", "0-3", "1-0"]  # GS evinde: W L D W L W
    matches = [match(GS, 10 + i, score, week=i) for i, score in enumerate(results)]

    [gs] = [r for r in calculate_standings(reversed(matches)) if r.team_id == GS]

    assert gs.form == [L, D, W, L, W]


def test_empty_input() -> None:
    assert calculate_standings([]) == []


class TestHeadToHead:
    def test_head_to_head_points_beat_overall_goal_difference(self) -> None:
        rows = calculate_standings(
            [
                match(GS, FB, "1-0", week=1),  # ikili: GS 4 puan, FB 1 puan
                match(FB, GS, "0-0", week=2),
                match(FB, TS, "5-0", week=3),
                match(TS, FB, "0-5", week=4),
                match(GS, TS, "1-0", week=5),
                match(TS, GS, "1-0", week=6),
            ]
        )

        gs, fb = rows[0], rows[1]
        assert (gs.team_id, gs.points, gs.goal_difference) == (GS, 7, 1)
        assert (fb.team_id, fb.points, fb.goal_difference) == (FB, 7, 9)

    def test_head_to_head_goal_difference_when_h2h_points_equal(self) -> None:
        rows = calculate_standings(
            [
                match(GS, FB, "3-0", week=1),  # ikili puan 3-3, ikili averaj GS +2
                match(FB, GS, "1-0", week=2),
                match(FB, TS, "6-0", week=3),  # FB genel averajda önde (+4 > +3)
                match(GS, TS, "1-0", week=4),
            ]
        )

        assert [r.team_id for r in rows[:2]] == [GS, FB]
        assert rows[0].goal_difference < rows[1].goal_difference

    def test_falls_back_to_overall_until_all_mutual_matches_played(self) -> None:
        # GS-FB rövanşı henüz oynanmadı → ikili kriter uygulanmaz, genel averaj belirler.
        rows = calculate_standings(
            [
                match(GS, FB, "1-0", week=1),
                match(FB, TS, "4-0", week=2),
                match(TS, GS, "1-0", week=3),
            ]
        )

        assert [r.team_id for r in rows] == [FB, GS, TS]

    def test_three_team_mini_league(self) -> None:
        # Kendi aralarında (ikili puan / ikili averaj): BJK 6 / +1, GS 5 / +1, FB 4 / -2
        mini_league = [
            match(GS, FB, "2-0", week=1),
            match(FB, GS, "1-0", week=2),
            match(GS, BJK, "1-1", week=3),
            match(BJK, GS, "0-0", week=4),
            match(FB, BJK, "0-1", week=5),
            match(BJK, FB, "2-2", week=6),
        ]
        # Puanları 7'de eşitleyen, her biri farklı rakiple oynanan maçlar
        others = [
            match(GS, 10, "2-2", week=7),
            match(GS, 11, "2-2", week=8),
            match(FB, 12, "1-0", week=7),
            match(BJK, 13, "0-0", week=7),
        ]

        rows = calculate_standings(mini_league + others)

        top = rows[:3]
        assert [r.points for r in top] == [7, 7, 7]
        # Genel kriterlerle GS önde olurdu (averaj eşit +1, atılan gol GS 7 > BJK 4);
        # ikili puan BJK'yi öne alır.
        assert [r.team_id for r in top] == [BJK, GS, FB]
