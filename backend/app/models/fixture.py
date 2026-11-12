from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import MatchStatus
from app.models.base import Base, ExternalIdMixin, TimestampMixin, str_enum
from app.models.team import Team

if TYPE_CHECKING:
    from app.models.fixture_change import FixtureChange
    from app.models.season import Season


class Fixture(Base, ExternalIdMixin, TimestampMixin):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"), index=True)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)

    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[MatchStatus] = mapped_column(str_enum(MatchStatus), index=True)
    status_raw: Mapped[str] = mapped_column(String(10))  # API'nin orijinal kodu: "FT", "NS"...
    home_goals: Mapped[int | None]
    away_goals: Mapped[int | None]
    round: Mapped[str | None] = mapped_column(String(50))

    season: Mapped["Season"] = relationship(back_populates="fixtures")
    home_team: Mapped[Team] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[Team] = relationship(foreign_keys=[away_team_id])
    changes: Mapped[list["FixtureChange"]] = relationship(back_populates="fixture")
