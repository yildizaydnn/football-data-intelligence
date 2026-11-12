from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, ExternalIdMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.season import Season


class League(Base, ExternalIdMixin, TimestampMixin):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(String(255))

    seasons: Mapped[list["Season"]] = relationship(back_populates="league")
