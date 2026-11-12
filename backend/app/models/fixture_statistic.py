from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class FixtureStatistic(Base, TimestampMixin):
    """Bir maçta bir takımın tek bir istatistiği (uzun format: yeni istatistik = yeni satır)."""

    __tablename__ = "fixture_statistics"
    __table_args__ = (
        UniqueConstraint("fixture_id", "team_id", "key", name="uq_fixture_statistics_entry"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    key: Mapped[str] = mapped_column(String(40))  # rules spec'teki anahtar, ör. shots_on_goal
    value: Mapped[float | None]
