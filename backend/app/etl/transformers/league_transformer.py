from datetime import date
from typing import Any

from app.etl.base import BaseTransformer, require
from app.providers.api_football.dto import LeagueDTO, SeasonInfo


class LeagueTransformer(BaseTransformer[LeagueDTO, dict[str, Any]]):
    def transform(self, item: LeagueDTO) -> dict[str, Any]:
        return {
            "external_id": require(item.league.id, "league.id"),
            "name": require(item.league.name, "league.name").strip(),
            "country": item.country.name,
            "logo_url": item.league.logo,
        }

    def external_id_of(self, item: LeagueDTO) -> int | None:
        return item.league.id


class SeasonTransformer(BaseTransformer[SeasonInfo, dict[str, Any]]):
    def __init__(self, league_id: int) -> None:
        self.league_id = league_id

    def transform(self, item: SeasonInfo) -> dict[str, Any]:
        return {
            "league_id": self.league_id,
            "year": require(item.year, "season.year"),
            "start_date": _parse_date(item.start),
            "end_date": _parse_date(item.end),
            "is_current": item.current,
        }


def _parse_date(value: str | None) -> date | None:
    # Sezon tarihleri bilgi amaçlı; bozuksa kaydı atlamak yerine boş bırakılır.
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
