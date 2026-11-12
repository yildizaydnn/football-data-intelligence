import pytest

from app.etl.transformers.statistics_transformer import StatisticsTransformer, parse_value
from app.providers.api_football.dto import TeamStatisticsDTO
from app.rules.engine import get_rule_engine
from tests.conftest import load_json

SPEC = get_rule_engine().resolve(203).cleaning.statistics
GS, IBFK = 645, 564  # gerçek yanıttaki takımlar


@pytest.mark.parametrize(
    ("raw", "null_as_zero", "expected"),
    [(9, False, 9.0), ("59%", False, 59.0), ("3.04", False, 3.04), (" 86 % ", False, 86.0),
     (None, True, 0.0), (None, False, None), ("", True, 0.0)],
)  # fmt: skip
def test_parse_value(raw, null_as_zero: bool, expected) -> None:
    assert parse_value(raw, null_as_zero) == expected


def test_parse_value_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_value("çok", False)


def test_real_response_is_cleaned_by_spec() -> None:
    dtos = [TeamStatisticsDTO.model_validate(t) for t in load_json("statistics.json")["response"]]

    result = StatisticsTransformer(7, {GS: 1, IBFK: 2}, SPEC).transform_many(dtos)

    home = {row["key"]: row["value"] for row in result.items[0]}
    away = {row["key"]: row["value"] for row in result.items[1]}
    assert len(home) == 17  # spec'teki istatistikler; "goals_prevented" spec'te yok → saklanmaz
    assert (home["possession"], away["possession"]) == (59.0, 41.0)
    assert home["expected_goals"] == 3.04
    assert home["red_cards"] == 0.0  # API null gönderdi, spec: null_as_zero
    assert home["shots_on_goal"] == 9.0
    assert {row["team_id"] for row in result.items[0]} == {1}
    assert "goals_prevented" not in home


def test_team_not_in_fixture_is_skipped() -> None:
    dtos = [TeamStatisticsDTO.model_validate(t) for t in load_json("statistics.json")["response"]]

    result = StatisticsTransformer(7, {GS: 1}, SPEC).transform_many(dtos)

    assert len(result.items) == 1
    assert "oynamıyor" in result.skipped[0].reason
