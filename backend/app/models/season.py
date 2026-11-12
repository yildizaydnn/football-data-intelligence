from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.fixture import Fixture
    from app.models.league import League


class Season(Base, TimestampMixin):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("league_id", "year", name="uq_seasons_league_id_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id", ondelete="CASCADE"))
    year: Mapped[int]
    start_date: Mapped[date | None]
    end_date: Mapped[date | None]
    is_current: Mapped[bool] = mapped_column(default=False)

    league: Mapped["League"] = relationship(back_populates="seasons")
    fixtures: Mapped[list["Fixture"]] = relationship(back_populates="season")
