from datetime import date

from sqlalchemy import Date
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class ApiUsage(Base, TimestampMixin):
    """Günlük API istek sayacı. Her gün için tek satır."""

    __tablename__ = "api_usage"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True)
    requests_used: Mapped[int] = mapped_column(default=0)
    daily_limit: Mapped[int]
    remaining: Mapped[int | None]  # API'nin x-ratelimit-requests-remaining header'ından
