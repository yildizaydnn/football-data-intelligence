from typing import ClassVar

from sqlalchemy import select

from app.models import Fixture, League, Season
from app.repositories.base import BaseRepository


class LeagueRepository(BaseRepository[League]):
    model = League


class SeasonRepository(BaseRepository[Season]):
    model = Season
    upsert_keys: ClassVar[tuple[str, ...]] = ("league_id", "year")

    def get_by_year(self, league_id: int, year: int) -> Season | None:
        stmt = select(Season).where(Season.league_id == league_id, Season.year == year)
        return self.session.scalar(stmt)

    def list_by_league(self, league_id: int) -> list[Season]:
        return self.list(Season.league_id == league_id, order_by=[Season.year.desc()])

    def list_with_fixtures(self, league_id: int) -> list[Season]:
        """En az bir maçı yüklenmiş sezonlar (yeniden eskiye)."""
        has_fixtures = select(Fixture.id).where(Fixture.season_id == Season.id).exists()
        return self.list(Season.league_id == league_id, has_fixtures, order_by=[Season.year.desc()])
