import logging
from collections.abc import Mapping
from typing import Any

from app.etl.base import BaseTransformer, TransformError, require
from app.providers.api_football.dto import TeamStatisticsDTO
from app.rules.models import StatisticSpec

logger = logging.getLogger(__name__)


class StatisticsTransformer(BaseTransformer[TeamStatisticsDTO, list[dict[str, Any]]]):
    """Bir takımın istatistik listesi → fixture_statistics satırları.

    Sağlayıcı adlarının anahtarlara eşlenmesi ve null yorumu ligin kural spec'inden gelir
    (cleaning.statistics). Spec'te olmayan istatistik saklanmaz.
    """

    def __init__(
        self,
        fixture_id: int,
        team_ids: Mapping[int, int],
        statistics: Mapping[str, StatisticSpec],
    ) -> None:
        self.fixture_id = fixture_id
        self.team_ids = team_ids
        self.statistics = statistics

    def transform(self, item: TeamStatisticsDTO) -> list[dict[str, Any]]:
        external_id = require(item.team.id, "team.id")
        team_id = self.team_ids.get(external_id)
        if team_id is None:
            raise TransformError(f"takım ({external_id}) bu maçta oynamıyor")

        rows = []
        for stat in item.statistics:
            spec = self.statistics.get(stat.type or "")
            if spec is None:
                continue
            try:
                value = parse_value(stat.value, spec.null_as_zero)
            except ValueError:
                logger.warning("İstatistik okunamadı: %s=%r", stat.type, stat.value)
                continue
            rows.append(
                {"fixture_id": self.fixture_id, "team_id": team_id, "key": spec.key, "value": value}
            )
        return rows

    def external_id_of(self, item: TeamStatisticsDTO) -> int | None:
        return item.team.id


def parse_value(raw: int | float | str | None, null_as_zero: bool) -> float | None:
    """9 → 9.0, "59%" → 59.0, "3.04" → 3.04, null → 0 ya da None."""
    if raw is None:
        return 0.0 if null_as_zero else None
    if isinstance(raw, int | float):
        return float(raw)
    text = raw.strip().rstrip("%").strip()
    if not text:
        return 0.0 if null_as_zero else None
    return float(text)
