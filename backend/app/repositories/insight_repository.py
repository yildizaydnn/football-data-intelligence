from datetime import datetime

from sqlalchemy import func, select

from app.models import TeamInsight
from app.repositories.base import BaseRepository


class InsightRepository(BaseRepository[TeamInsight]):
    model = TeamInsight

    def get_for_pair(self, season_id: int, team_a_id: int, team_b_id: int) -> TeamInsight | None:
        stmt = select(TeamInsight).where(
            TeamInsight.season_id == season_id,
            TeamInsight.team_a_id == team_a_id,
            TeamInsight.team_b_id == team_b_id,
        )
        return self.session.scalar(stmt)

    def count_generated_since(self, since: datetime) -> int:
        stmt = (
            select(func.count()).select_from(TeamInsight).where(TeamInsight.generated_at >= since)
        )
        return self.session.scalar(stmt) or 0
