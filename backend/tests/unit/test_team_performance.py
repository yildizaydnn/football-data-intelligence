import pytest

from app.analytics.team_performance import calculate_team_performance
from app.core.enums import MatchResult
from tests.unit.analytics_helpers import match

W, D, L = MatchResult.WIN, MatchResult.DRAW, MatchResult.LOSS
GS, FB, BJK, TS = 1, 2, 3, 4

SEASON = [
    match(GS, FB, "2-0", week=1),  # iç saha W
    match(BJK, GS, "1-1", week=2),  # deplasman D
    match(GS, TS, "0-1", week=3),  # iç saha L
    match(TS, GS, "0-3", week=4),  # deplasman W
    match(FB, BJK, "2-2", week=5),  # GS oynamadı
    match(GS, BJK, None, week=6),  # henüz oynanmadı
]


def test_overall_totals_and_rates() -> None:
    overall = calculate_team_performance(GS, SEASON).overall

    assert (overall.played, overall.won, overall.drawn, overall.lost) == (4, 2, 1, 1)
    assert (overall.goals_for, overall.goals_against, overall.points) == (6, 2, 7)
    assert overall.win_rate == pytest.approx(0.5)
    assert overall.draw_rate == pytest.approx(0.25)
    assert overall.avg_goals_for == pytest.approx(1.5)
    assert overall.avg_goals_against == pytest.approx(0.5)
    assert overall.points_per_game == pytest.approx(1.75)
    assert (overall.clean_sheets, overall.failed_to_score) == (2, 1)


def test_home_and_away_split() -> None:
    perf = calculate_team_performance(GS, SEASON)

    assert (perf.home.played, perf.home.won, perf.home.lost) == (2, 1, 1)
    assert (perf.home.goals_for, perf.home.goals_against) == (2, 1)
    assert (perf.away.played, perf.away.won, perf.away.drawn) == (2, 1, 1)
    assert (perf.away.goals_for, perf.away.goals_against) == (4, 1)


def test_form_and_timeline() -> None:
    perf = calculate_team_performance(GS, SEASON)

    assert perf.form == [W, D, L, W]
    assert [p.cumulative_points for p in perf.timeline] == [3, 4, 4, 7]
    assert [p.opponent_id for p in perf.timeline] == [FB, BJK, TS, TS]
    assert [p.is_home for p in perf.timeline] == [True, False, True, False]
    assert perf.current_streak == (W, 1)


def test_current_streak_counts_consecutive_results() -> None:
    perf = calculate_team_performance(
        GS, [match(GS, FB, "0-1", 1), match(GS, BJK, "2-0", 2), match(TS, GS, "1-2", 3)]
    )

    assert perf.current_streak == (W, 2)


def test_team_without_matches_has_zero_rates() -> None:
    perf = calculate_team_performance(99, SEASON)

    assert perf.overall.played == 0
    assert perf.overall.win_rate == 0.0
    assert perf.overall.avg_goals_for == 0.0
    assert perf.form == []
    assert perf.current_streak is None
