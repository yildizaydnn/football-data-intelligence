from collections.abc import Iterable

from sqlalchemy import or_, select

from app.models import Fixture, Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    model = Team

    def list_by_season(self, season_id: int, round_pattern: str | None = None) -> list[Team]:
        """Sezonda en az bir maçı olan takımlar.

        `round_pattern` (PostgreSQL regex) verilirse yalnızca eşleşen haftalardaki maçlar sayılır;
        ör. küme düşme play-off'una katılan alt lig takımı lig tablosuna girmez.
        """
        conditions = [
            Fixture.season_id == season_id,
            or_(Fixture.home_team_id == Team.id, Fixture.away_team_id == Team.id),
        ]
        if round_pattern:
            conditions.append(Fixture.round.regexp_match(round_pattern))
        in_season = select(Fixture.id).where(*conditions)
        return self.list(in_season.exists(), order_by=[Team.name])

    def list_by_ids(self, ids: Iterable[int]) -> list[Team]:
        ids = set(ids)
        return self.list(Team.id.in_(ids)) if ids else []
