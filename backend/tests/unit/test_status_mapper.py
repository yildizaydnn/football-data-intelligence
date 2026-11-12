import pytest

from app.core.enums import MatchStatus
from app.core.status_mapper import UnknownStatusError, map_status


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("NS", MatchStatus.SCHEDULED),
        ("TBD", MatchStatus.SCHEDULED),
        ("1H", MatchStatus.LIVE),
        ("HT", MatchStatus.LIVE),
        ("2H", MatchStatus.LIVE),
        ("ET", MatchStatus.LIVE),
        ("P", MatchStatus.LIVE),
        ("SUSP", MatchStatus.LIVE),
        ("FT", MatchStatus.FINISHED),
        ("AET", MatchStatus.FINISHED),
        ("PEN", MatchStatus.FINISHED),
        ("AWD", MatchStatus.FINISHED),
        ("WO", MatchStatus.FINISHED),
        ("PST", MatchStatus.POSTPONED),
        ("CANC", MatchStatus.CANCELLED),
        ("ABD", MatchStatus.CANCELLED),
    ],
)
def test_known_codes(raw: str, expected: MatchStatus) -> None:
    assert map_status(raw) is expected


def test_is_case_and_whitespace_insensitive() -> None:
    assert map_status(" ft ") is MatchStatus.FINISHED


@pytest.mark.parametrize("raw", ["XYZ", "", None])
def test_unknown_code_raises(raw: str | None) -> None:
    with pytest.raises(UnknownStatusError):
        map_status(raw)
