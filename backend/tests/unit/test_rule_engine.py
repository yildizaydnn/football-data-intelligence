from pathlib import Path

import pytest
import yaml

from app.core.enums import MatchStatus
from app.rules.engine import DEFAULT_SPEC_DIR, RuleEngine, RuleSpecError

DEFAULT = yaml.safe_load((DEFAULT_SPEC_DIR / "default.yaml").read_text(encoding="utf-8"))


def _write_specs(tmp_path: Path, leagues: dict[str, dict], default: dict | None = None) -> Path:
    (tmp_path / "leagues").mkdir(parents=True)
    (tmp_path / "default.yaml").write_text(yaml.safe_dump(default or DEFAULT), encoding="utf-8")
    for name, spec in leagues.items():
        (tmp_path / "leagues" / f"{name}.yaml").write_text(yaml.safe_dump(spec), encoding="utf-8")
    return tmp_path


def test_real_spec_files_are_valid() -> None:
    engine = RuleEngine()  # açılışta tüm lig × sezon kombinasyonlarını doğrular

    assert 203 in engine.configured_leagues


def test_layers_merge_default_league_and_season(tmp_path: Path) -> None:
    engine = RuleEngine(
        _write_specs(
            tmp_path,
            {
                "1-test": {
                    "league": 1,
                    "meta": {"name": "Test Ligi", "verified": False},
                    "standings": {"tiebreakers": ["points", "h2h_points"]},
                    "cleaning": {"status_map": {"XYZ": "postponed"}},
                    "seasons": {2024: {"standings": {"deductions": {77: 3}}}},
                }
            },
        )
    )

    base = engine.resolve(1)
    season = engine.resolve(1, 2024)

    assert base.meta.name == "Test Ligi"
    assert base.standings.tiebreakers == ["points", "h2h_points"]  # listeler değişir
    assert base.standings.points.win == 3  # default'tan
    assert base.cleaning.status_map["FT"] is MatchStatus.FINISHED  # default korunur
    assert base.cleaning.status_map["XYZ"] is MatchStatus.POSTPONED  # lig eklentisi
    assert base.standings.deductions == {}
    assert season.standings.deductions == {77: 3}  # sezon katmanı
    assert season.standings.tiebreakers == ["points", "h2h_points"]


def test_unknown_league_falls_back_to_default(tmp_path: Path) -> None:
    engine = RuleEngine(_write_specs(tmp_path, {}))

    assert engine.resolve(999, 2024).meta.name == DEFAULT["meta"]["name"]


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"standings": {"tiebreakers": ["points", "coin_toss"]}}, "coin_toss"),
        ({"standings": {"include_rounds": "([unclosed"}}, "include_rounds"),
        ({"standings": {"deductions": {5: -3}}}, "negatif"),
        ({"standings": {"pointz": {"win": 3}}}, "pointz"),  # yazım hatası
        ({"cleaning": {"status_map": {"FT": "done"}}}, "status_map"),
        ({"zones": [{"from": 1, "to": -1, "kind": "relegation", "label": "x"}]}, "aynı uçtan"),
    ],
)
def test_invalid_specs_fail_at_startup(tmp_path: Path, override: dict, message: str) -> None:
    spec = {"league": 1, **override}

    with pytest.raises(RuleSpecError, match=message):
        RuleEngine(_write_specs(tmp_path, {"1-bad": spec}))


def test_invalid_season_override_fails_even_if_never_requested(tmp_path: Path) -> None:
    spec = {"league": 1, "seasons": {2022: {"standings": {"tiebreakers": ["nope"]}}}}

    with pytest.raises(RuleSpecError, match="sezon=2022"):
        RuleEngine(_write_specs(tmp_path, {"1-bad": spec}))


def test_league_id_is_required_and_unique(tmp_path: Path) -> None:
    with pytest.raises(RuleSpecError, match="zorunlu"):
        RuleEngine(_write_specs(tmp_path / "a", {"x": {"meta": {"name": "x", "verified": False}}}))
    with pytest.raises(RuleSpecError, match="birden fazla"):
        RuleEngine(_write_specs(tmp_path / "b", {"a": {"league": 5}, "b": {"league": 5}}))


def test_zones_count_from_top_and_bottom(tmp_path: Path) -> None:
    zones = [
        {"from": 1, "to": 4, "kind": "champions_league", "label": "ŞL"},
        {"from": -3, "to": -1, "kind": "relegation", "label": "Düşme"},
    ]
    engine = RuleEngine(_write_specs(tmp_path, {"1-z": {"league": 1, "zones": zones}}))
    ctx = engine.resolve(1)

    assert ctx.zone_for(1, 20).label == "ŞL"
    assert ctx.zone_for(5, 20) is None
    assert ctx.zone_for(18, 20).label == "Düşme"
    assert ctx.zone_for(17, 20) is None
    assert ctx.zone_for(16, 18).label == "Düşme"  # 18 takımlı sezonda aynı spec


def test_standings_rules_map_deductions_to_internal_ids(tmp_path: Path) -> None:
    spec = {"league": 1, "standings": {"deductions": {611: 6, 999: 3}}}
    ctx = RuleEngine(_write_specs(tmp_path, {"1-d": spec})).resolve(1)

    rules = ctx.standings_rules({611: 42})  # 999 bu sezonda yok → yok sayılır

    assert dict(rules.deductions) == {42: 6}
