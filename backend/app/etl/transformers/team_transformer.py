from typing import Any

from app.etl.base import BaseTransformer, require
from app.providers.api_football.dto import TeamDTO

MAX_CODE_LENGTH = 10


class TeamTransformer(BaseTransformer[TeamDTO, dict[str, Any]]):
    def transform(self, item: TeamDTO) -> dict[str, Any]:
        code = (item.team.code or "").strip().upper() or None
        return {
            "external_id": require(item.team.id, "team.id"),
            "name": require(item.team.name, "team.name").strip(),
            "code": code if code and len(code) <= MAX_CODE_LENGTH else None,
            "logo_url": item.team.logo,
            "venue_name": item.venue.name,
        }

    def external_id_of(self, item: TeamDTO) -> int | None:
        return item.team.id
