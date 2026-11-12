from dataclasses import dataclass

from app.analytics.season_summary import summarize_season
from app.core.enums import MatchStatus
from tests.unit.analytics_helpers import Match, match


@dataclass(frozen=True)
class StatusMatch(Match):
    status: MatchStatus = MatchStatus.FINISHED


def _with(m: Match, status: MatchStatus, round: str | None = None) -> StatusMatch:
    return StatusMatch(**{**vars(m), "round": round}, status=status)


def test_summary_counts_only_finished_matches_for_goals_and_results() -> None:
    summary = summarize_season(
        [
            _with(match(1, 2, "2-1", week=1), MatchStatus.FINISHED),
            _with(match(3, 4, "0-0", week=1), MatchStatus.FINISHED),
            _with(match(2, 3, "0-3", week=2), MatchStatus.FINISHED),
            _with(match(4, 1, "5-0", week=3), MatchStatus.LIVE),  # anlık skor sayılmaz
            _with(match(1, 3, None, week=4), MatchStatus.SCHEDULED),
        ]
    )

    assert summary.total_matches == 5
    assert summary.by_status[MatchStatus.FINISHED] == 3
    assert summary.by_status[MatchStatus.CANCELLED] == 0
    assert (summary.home_wins, summary.draws, summary.away_wins) == (1, 1, 1)
    assert summary.total_goals == 6
    assert summary.avg_goals_per_match == 2.0
    assert summary.home_win_rate == summary.away_win_rate == 1 / 3


def test_goals_by_round_ordered_by_round_number() -> None:
    summary = summarize_season(
        [
            _with(match(1, 2, "2-1", week=1), MatchStatus.FINISHED, "Regular Season - 1"),
            _with(match(3, 4, "1-1", week=1), MatchStatus.FINISHED, "Regular Season - 1"),
            _with(match(1, 3, "0-1", week=2), MatchStatus.FINISHED, "Regular Season - 2"),
            # 10. haftanın ertelenmiş maçı 2. haftadan önce oynanmış olsa da sıra bozulmaz
            _with(match(2, 4, "3-0", week=0), MatchStatus.FINISHED, "Regular Season - 10"),
            _with(match(4, 1, None, week=3), MatchStatus.SCHEDULED, "Regular Season - 3"),
        ]
    )

    assert [(r.number, r.matches, r.goals) for r in summary.goals_by_round] == [
        (1, 2, 5),
        (2, 1, 1),
        (10, 1, 3),
    ]
    assert summary.current_round.number == 10


def test_rounds_without_number_go_last() -> None:
    summary = summarize_season(
        [
            _with(match(1, 2, "1-0", week=5), MatchStatus.FINISHED, "Play-offs"),
            _with(match(3, 4, "2-0", week=1), MatchStatus.FINISHED, "Regular Season - 34"),
        ]
    )

    assert [(r.round, r.number) for r in summary.goals_by_round] == [
        ("Regular Season - 34", 34),
        ("Play-offs", None),
    ]


def test_empty_season() -> None:
    summary = summarize_season([])

    assert summary.total_matches == 0
    assert summary.avg_goals_per_match == 0.0
    assert summary.home_win_rate == 0.0
    assert summary.goals_by_round == []
    assert summary.current_round is None
