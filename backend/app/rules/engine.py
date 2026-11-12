"""Kural motoru: YAML spec katmanlarını birleştirip lig + sezon için RuleContext üretir.

    specs/default.yaml              → tüm liglerin temeli
    specs/leagues/<id>-<ad>.yaml    → lig farkları (`league: <API id>`);
                                      `seasons:` altında sezon farkları

Birleştirme: sözlükler derinlemesine birleşir, listeler (tiebreakers, zones) tamamen değişir.
Tüm lig × sezon kombinasyonları açılışta doğrulanır; hatalı spec uygulamayı başlatmaz.
"""

import copy
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from app.rules.models import RuleContext

DEFAULT_SPEC_DIR = Path(__file__).parent / "specs"


class RuleSpecError(ValueError):
    pass


class RuleEngine:
    def __init__(self, spec_dir: Path = DEFAULT_SPEC_DIR) -> None:
        self._default = _load(spec_dir / "default.yaml")
        self._leagues: dict[int, dict[str, Any]] = {}
        for path in sorted((spec_dir / "leagues").glob("*.yaml")):
            spec = _load(path)
            league_id = spec.pop("league", None)
            if not isinstance(league_id, int):
                raise RuleSpecError(f"{path.name}: 'league' (API lig id'si) zorunlu")
            if league_id in self._leagues:
                raise RuleSpecError(f"{path.name}: lig {league_id} için birden fazla spec")
            self._leagues[league_id] = spec
        self._cache: dict[tuple[int | None, int | None], RuleContext] = {}
        self.validate_all()

    @property
    def configured_leagues(self) -> list[int]:
        return sorted(self._leagues)

    def resolve(self, league_external_id: int | None, season: int | None = None) -> RuleContext:
        """Spec'i olmayan lig için varsayılan kurallar döner (ör. yeni eklenen bir lig)."""
        key = (league_external_id, season)
        if key not in self._cache:
            self._cache[key] = self._build(league_external_id, season)
        return self._cache[key]

    def validate_all(self) -> None:
        self.resolve(None)
        for league_id, spec in self._leagues.items():
            self.resolve(league_id)
            for season in spec.get("seasons", {}):
                self.resolve(league_id, season)

    def _build(self, league_external_id: int | None, season: int | None) -> RuleContext:
        merged = copy.deepcopy(self._default)
        league = copy.deepcopy(self._leagues.get(league_external_id or -1, {}))
        seasons = league.pop("seasons", {}) or {}
        merged = _deep_merge(merged, league)
        if season is not None and season in seasons:
            merged = _deep_merge(merged, seasons[season])
        try:
            return RuleContext.model_validate(
                {**merged, "league_external_id": league_external_id, "season": season}
            )
        except ValueError as exc:
            raise RuleSpecError(
                f"Geçersiz kural spec'i (lig={league_external_id}, sezon={season}): {exc}"
            ) from exc


def _load(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuleSpecError(f"{path.name} okunamadı: {exc}") from exc
    if not isinstance(data, dict):
        raise RuleSpecError(f"{path.name}: kök bir sözlük olmalı")
    return data


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = _deep_merge(dict(result[key]), value)
        else:
            result[key] = copy.deepcopy(value)
    return result


@lru_cache
def get_rule_engine() -> RuleEngine:
    return RuleEngine()
