from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.enums import SyncStatus, SyncTrigger
from app.models import SyncRun
from app.repositories.base import BaseRepository


class SyncRunRepository(BaseRepository[SyncRun]):
    model = SyncRun

    def try_start(self, trigger: SyncTrigger) -> SyncRun | None:
        """RUNNING kaydı açar. Zaten çalışan bir sync varsa None döner.

        Kontrolü kısmi unique index yapar; iki istek aynı anda gelse bile yalnızca biri başlar.
        """
        run = SyncRun(trigger=trigger, status=SyncStatus.RUNNING)
        try:
            with self.session.begin_nested():
                self.session.add(run)
        except IntegrityError:
            return None
        return run

    def get_running(self) -> SyncRun | None:
        return self.session.scalar(select(SyncRun).where(SyncRun.status == SyncStatus.RUNNING))

    def latest(self) -> SyncRun | None:
        stmt = select(SyncRun).order_by(SyncRun.started_at.desc(), SyncRun.id.desc()).limit(1)
        return self.session.scalar(stmt)

    def list_recent(self, limit: int = 10) -> list[SyncRun]:
        return self.list(order_by=[SyncRun.started_at.desc(), SyncRun.id.desc()], limit=limit)

    def finish(
        self,
        run: SyncRun,
        status: SyncStatus,
        *,
        requests_made: int = 0,
        inserted: int = 0,
        updated: int = 0,
        skipped: int = 0,
        error_message: str | None = None,
    ) -> SyncRun:
        run.status = status
        run.finished_at = _now()
        run.requests_made = requests_made
        run.inserted = inserted
        run.updated = updated
        run.skipped = skipped
        run.error_message = error_message
        self.session.flush()
        return run

    def fail_stale(self, started_before: datetime) -> int:
        """Süreç çöktüğü için RUNNING'de asılı kalan kayıtları FAILED yapar (kilidi açar)."""
        stmt = (
            update(SyncRun)
            .where(SyncRun.status == SyncStatus.RUNNING, SyncRun.started_at < started_before)
            .values(
                status=SyncStatus.FAILED,
                finished_at=_now(),
                error_message="Stale run: zaman aşımı nedeniyle sonlandırıldı",
            )
        )
        return self.session.execute(stmt).rowcount


def _now() -> datetime:
    return datetime.now(UTC)
