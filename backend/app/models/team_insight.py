from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TeamInsight(Base):
    """AI ile üretilmiş iki takım karşılaştırması (önbellek).

    Takım çifti sıralı saklanır (team_a_id < team_b_id); veri değişince (facts_hash)
    yeniden üretilir.
    """

    __tablename__ = "team_insights"
    __table_args__ = (
        UniqueConstraint("season_id", "team_a_id", "team_b_id", name="uq_team_insights_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id", ondelete="CASCADE"))
    team_a_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    team_b_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    facts_hash: Mapped[str] = mapped_column(String(64))
    facts: Mapped[dict] = mapped_column(JSON)  # LLM'e verilen veri (şeffaflık için saklanır)
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(60))
    unverified_numbers: Mapped[list[str]] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
