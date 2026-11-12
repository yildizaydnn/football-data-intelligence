from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import SyncStatus, SyncTrigger
from app.models.base import Base, str_enum


class SyncRun(Base):
    """Her senkronizasyon çalışmasının kaydı. RUNNING kaydı aynı anda ikinci sync'i engeller."""

    __tablename__ = "sync_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    trigger: Mapped[SyncTrigger] = mapped_column(str_enum(SyncTrigger))
    status: Mapped[SyncStatus] = mapped_column(
        str_enum(SyncStatus), default=SyncStatus.RUNNING, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    requests_made: Mapped[int] = mapped_column(default=0)
    inserted: Mapped[int] = mapped_column(default=0)
    updated: Mapped[int] = mapped_column(default=0)
    skipped: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
