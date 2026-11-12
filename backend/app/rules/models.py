"""Lig kuralı spec modelleri.

YAML dosyaları bu şemaya göre doğrulanır; yazım hatası uygulama açılırken hata verir.
"""

import re
from collections.abc import Mapping
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.analytics.common import PointsTable
from app.analytics.standings import StandingsRules
from app.analytics.tiebreakers import CRITERIA, HeadToHeadOptions
from app.core.enums import MatchStatus


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class PointsSpec(_Spec):
    win: int
    draw: int
    loss: int


class HeadToHeadSpec(_Spec):
    requires_all_matches: bool
    matches_per_pair: int = Field(ge=1)
    reapply_to_subgroups: bool


class StandingsSpec(_Spec):
    points: PointsSpec
    tiebreakers: list[str] = Field(min_length=1)
    head_to_head: HeadToHeadSpec
    include_rounds: str | None  # regex; null → tüm haftalar
    deductions: dict[int, int]  # takımın API (external) id'si → silinen puan

    @field_validator("tiebreakers")
    @classmethod
    def _known_criteria(cls, value: list[str]) -> list[str]:
        unknown = [name for name in value if name not in CRITERIA]
        if unknown:
            raise ValueError(f"bilinmeyen sıralama kriteri: {unknown}; geçerli: {sorted(CRITERIA)}")
        return value

    @field_validator("include_rounds")
    @classmethod
    def _valid_regex(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                re.compile(value)
            except re.error as exc:  # re.error ValueError değil; pydantic'e doğrulama hatası ver
                raise ValueError(f"geçersiz regex: {exc}") from exc
        return value

    @field_validator("deductions")
    @classmethod
    def _non_negative(cls, value: dict[int, int]) -> dict[int, int]:
        if any(points < 0 for points in value.values()):
            raise ValueError("puan silme cezası negatif olamaz")
        return value


class StatisticSpec(_Spec):
    key: str = Field(pattern=r"^[a-z][a-z_]*$")  # bizim anahtarımız, ör. shots_on_goal
    null_as_zero: bool = False  # sağlayıcı "olmadı" anlamında null gönderiyorsa


class CleaningSpec(_Spec):
    status_map: dict[str, MatchStatus]  # sağlayıcı kodu ("FT") → durum
    # Sağlayıcı istatistik adı → anahtar. Sıra arayüzdeki gösterim sırasıdır;
    # listede olmayan istatistikler saklanmaz.
    statistics: dict[str, StatisticSpec]

    @field_validator("statistics")
    @classmethod
    def _unique_keys(cls, value: dict[str, StatisticSpec]) -> dict[str, StatisticSpec]:
        keys = [spec.key for spec in value.values()]
        if len(keys) != len(set(keys)):
            raise ValueError("istatistik anahtarları benzersiz olmalı")
        return value

    @field_validator("status_map")
    @classmethod
    def _upper_keys(cls, value: dict[str, MatchStatus]) -> dict[str, MatchStatus]:
        return {key.strip().upper(): status for key, status in value.items()}


class ZoneKind(StrEnum):
    CHAMPIONS_LEAGUE = "champions_league"
    EUROPA_LEAGUE = "europa_league"
    CONFERENCE_LEAGUE = "conference_league"
    RELEGATION_PLAYOFF = "relegation_playoff"
    RELEGATION = "relegation"


class Zone(_Spec):
    """Tablo bölgesi. Pozitif sıra üstten (1 = lider), negatif sıra alttan (-1 = son)."""

    from_position: int = Field(alias="from")
    to_position: int = Field(alias="to")
    kind: ZoneKind
    label: str

    @model_validator(mode="after")
    def _same_side(self) -> "Zone":
        if 0 in (self.from_position, self.to_position):
            raise ValueError("sıra 0 olamaz")
        if (self.from_position > 0) != (self.to_position > 0):
            raise ValueError("bölge sınırları aynı uçtan sayılmalı")
        return self

    def contains(self, position: int, total: int) -> bool:
        start, end = (self._absolute(p, total) for p in (self.from_position, self.to_position))
        return min(start, end) <= position <= max(start, end)

    @staticmethod
    def _absolute(position: int, total: int) -> int:
        return position if position > 0 else total + position + 1


class SpecMeta(_Spec):
    name: str
    sources: list[str] = []
    verified: bool  # değerler resmi yönetmelikle karşılaştırıldı mı
    notes: str | None = None


class RuleContext(_Spec):
    """Bir lig + sezon için birleştirilmiş, doğrulanmış kurallar (default ← lig ← sezon)."""

    league_external_id: int | None
    season: int | None
    meta: SpecMeta
    standings: StandingsSpec
    cleaning: CleaningSpec
    zones: list[Zone]

    @property
    def points_table(self) -> PointsTable:
        p = self.standings.points
        return PointsTable(win=p.win, draw=p.draw, loss=p.loss)

    def standings_rules(self, team_ids: Mapping[int, int]) -> StandingsRules:
        """Analytics'e verilecek saf kurallar. `team_ids`: external id → iç id (cezalar için)."""
        s = self.standings
        return StandingsRules(
            points=self.points_table,
            tiebreakers=tuple(s.tiebreakers),
            head_to_head=HeadToHeadOptions(
                requires_all_matches=s.head_to_head.requires_all_matches,
                matches_per_pair=s.head_to_head.matches_per_pair,
                reapply_to_subgroups=s.head_to_head.reapply_to_subgroups,
            ),
            round_pattern=s.include_rounds,
            deductions={
                team_ids[external_id]: points
                for external_id, points in s.deductions.items()
                if external_id in team_ids
            },
        )

    def zone_for(self, position: int, total: int) -> Zone | None:
        return next((z for z in self.zones if z.contains(position, total)), None)
