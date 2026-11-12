from collections.abc import Iterable

from sqlalchemy import or_, select

from app.models import Fixture, Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    model = Team

    def list_by_season(self, season_id: int) -> list[Team]:
        """Sezonda en az bir maçı olan takımlar."""
        in_season = select(Fixture.id).where(
            Fixture.season_id == season_id,
            or_(Fixture.home_team_id == Team.id, Fixture.away_team_id == Team.id),
        )
        return self.list(in_season.exists(), order_by=[Team.name])

    def list_by_ids(self, ids: Iterable[int]) -> list[Team]:
        ids = set(ids)
        return self.list(Team.id.in_(ids)) if ids else []
