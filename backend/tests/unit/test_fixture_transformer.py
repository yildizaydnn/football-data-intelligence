import copy
from datetime import UTC, datetime
from typing import Any

import pytest

from app.core.enums import MatchStatus
from app.etl.transformers.fixture_transformer import FixtureTransformer
from app.providers.api_football.dto import FixtureDTO
from tests.conftest import load_json

SEASON_ID = 7
# external_id → iç id
TEAM_IDS = {645: 1, 611: 2, 549: 3, 998: 4}


@pytest.fixture
def raw_fixtures() -> list[dict[str, Any]]:
    return load_json("fixtures.json")["response"]


@pytest.fixture
def transformer() -> FixtureTransformer:
    return FixtureTransformer(SEASON_ID, TEAM_IDS)


def _dto(raw: list[dict[str, Any]], external_id: int, **patch: Any) -> FixtureDTO:
    item = copy.deepcopy(next(f for f in raw if f["fixture"]["id"] == external_id))
    for path, value in patch.items():
        *parents, leaf = path.split("__")
        target = item
        for key in parents:
            target = target[key]
        target[leaf] = value
    return FixtureDTO.model_validate(item)


def test_transform_many_skips_invalid_and_keeps_rest(
    transformer: FixtureTransformer, raw_fixtures: list[dict[str, Any]]
) -> None:
    result = transformer.transform_many([FixtureDTO.model_validate(f) for f in raw_fixtures])

    assert [i["external_id"] for i in result.items] == [1001, 1002, 1003, 1004, 1005]
    [skipped] = result.skipped
    assert skipped.external_id == 1006
    assert "teams.home.id" in skipped.reason


def test_finished_match(transformer: FixtureTransformer, raw_fixtures: list) -> None:
    row = transformer.transform(_dto(raw_fixtures, 1001))

    assert row == {
        "external_id": 1001,
        "season_id": SEASON_ID,
        "home_team_id": 1,
        "away_team_id": 2,
        "kickoff_at": datetime(2024, 9, 21, 16, 0, tzinfo=UTC),
        "status": MatchStatus.FINISHED,
        "status_raw": "FT",
        "home_goals": 1,
        "away_goals": 3,
        "round": "Regular Season - 6",
    }


def test_live_match_keeps_current_score(transformer: FixtureTransformer, raw_fixtures: list):
    row = transformer.transform(_dto(raw_fixtures, 1003))

    assert (row["status"], row["home_goals"], row["away_goals"]) == (MatchStatus.LIVE, 2, 0)


def test_scheduled_match_has_null_score(transformer: FixtureTransformer, raw_fixtures: list):
    row = transformer.transform(_dto(raw_fixtures, 1004))

    assert row["status"] is MatchStatus.SCHEDULED
    assert (row["home_goals"], row["away_goals"]) == (None, None)


def test_postponed_match_drops_score_even_if_api_sends_one(
    transformer: FixtureTransformer, raw_fixtures: list
) -> None:
    row = transformer.transform(_dto(raw_fixtures, 1005, goals__home=0, goals__away=0))

    assert row["status"] is MatchStatus.POSTPONED
    assert row["home_goals"] is None


def test_kickoff_is_normalized_to_utc(transformer: FixtureTransformer, raw_fixtures: list):
    row = transformer.transform(_dto(raw_fixtures, 1001, fixture__date="2024-09-21T19:00:00+03:00"))

    assert row["kickoff_at"] == datetime(2024, 9, 21, 16, 0, tzinfo=UTC)
    assert row["kickoff_at"].utcoffset().total_seconds() == 0


def test_naive_date_is_treated_as_utc(transformer: FixtureTransformer, raw_fixtures: list):
    row = transformer.transform(_dto(raw_fixtures, 1001, fixture__date="2024-09-21T16:00:00"))

    assert row["kickoff_at"] == datetime(2024, 9, 21, 16, 0, tzinfo=UTC)


def test_falls_back_to_timestamp(transformer: FixtureTransformer, raw_fixtures: list):
    row = transformer.transform(_dto(raw_fixtures, 1001, fixture__date=None))

    assert row["kickoff_at"] == datetime(2024, 9, 21, 16, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("patch", "reason"),
    [
        ({"fixture__id": None}, "fixture.id"),
        ({"fixture__status__short": "XYZ"}, "bilinmeyen durum"),
        ({"fixture__date": "dün akşam"}, "geçersiz tarih"),
        ({"fixture__date": None, "fixture__timestamp": None}, "fixture.date"),
        ({"teams__away__id": 12345}, "veritabanında yok"),
        ({"teams__away__id": 645}, "aynı takım"),
        ({"goals__home": None, "goals__away": None}, "skoru yok"),
        ({"goals__away": None}, "bir tarafı"),
        ({"goals__home": -1}, "negatif"),
    ],
)
def test_invalid_records_are_skipped(
    transformer: FixtureTransformer, raw_fixtures: list, patch: dict[str, Any], reason: str
) -> None:
    result = transformer.transform_many([_dto(raw_fixtures, 1001, **patch)])

    assert result.items == []
    [skipped] = result.skipped
    assert reason in skipped.reason


def test_unexpected_error_does_not_crash_batch(raw_fixtures: list) -> None:
    class BrokenMap(dict):
        def __getitem__(self, key: int) -> int:
            raise RuntimeError("beklenmeyen")

    result = FixtureTransformer(SEASON_ID, BrokenMap()).transform_many(
        [_dto(raw_fixtures, 1001), _dto(raw_fixtures, 1002)]
    )

    assert result.items == []
    assert len(result.skipped) == 2
    assert "beklenmeyen hata" in result.skipped[0].reason
