from typing import ClassVar

from sqlalchemy import select

from app.models import FixtureStatistic
from app.repositories.base import BaseRepository


class StatisticsRepository(BaseRepository[FixtureStatistic]):
    model = FixtureStatistic
    upsert_keys: ClassVar[tuple[str, ...]] = ("fixture_id", "team_id", "key")

    def list_for_fixture(self, fixture_id: int) -> list[FixtureStatistic]:
        stmt = select(FixtureStatistic).where(FixtureStatistic.fixture_id == fixture_id)
        return list(self.session.scalars(stmt))
