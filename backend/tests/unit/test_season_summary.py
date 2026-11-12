from dataclasses import dataclass

from app.analytics.season_summary import summarize_season
from app.core.enums import MatchStatus
from tests.unit.analytics_helpers import Match, match


@dataclass(frozen=True)
class StatusMatch(Match):
    status: MatchStatus = MatchStatus.FINISHED


def _with_status(m: Match, status: MatchStatus) -> StatusMatch:
    return StatusMatch(**vars(m), status=status)


def test_summary_counts_only_finished_matches_for_goals_and_results() -> None:
    summary = summarize_season(
        [
            _with_status(match(1, 2, "2-1", week=1), MatchStatus.FINISHED),
            _with_status(match(3, 4, "0-0", week=1), MatchStatus.FINISHED),
            _with_status(match(2, 3, "0-3", week=2), MatchStatus.FINISHED),
            _with_status(match(4, 1, "5-0", week=3), MatchStatus.LIVE),  # anlık skor sayılmaz
            _with_status(match(1, 3, None, week=4), MatchStatus.SCHEDULED),
        ]
    )

    assert summary.total_matches == 5
    assert summary.by_status[MatchStatus.FINISHED] == 3
    assert summary.by_status[MatchStatus.CANCELLED] == 0
    assert (summary.home_wins, summary.draws, summary.away_wins) == (1, 1, 1)
    assert summary.total_goals == 6
    assert summary.avg_goals_per_match == 2.0
    assert summary.home_win_rate == summary.away_win_rate == 1 / 3


def test_empty_season() -> None:
    summary = summarize_season([])

    assert summary.total_matches == 0
    assert summary.avg_goals_per_match == 0.0
    assert summary.home_win_rate == 0.0
