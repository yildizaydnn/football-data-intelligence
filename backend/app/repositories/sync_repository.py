from datetime import timedelta

from sqlalchemy import func, select, update
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

    def record_skipped(self, trigger: SyncTrigger, reason: str) -> SyncRun:
        """İstek atılmadan atlanan sync'i kaydeder (kilit almaz; geçmişte görünsün diye)."""
        run = SyncRun(
            trigger=trigger,
            status=SyncStatus.SKIPPED,
            finished_at=func.now(),
            error_message=reason,
        )
        self.session.add(run)
        self.session.flush()
        self._load_timestamps(run)
        return run

    def get_running(self) -> SyncRun | None:
        return self.session.scalar(select(SyncRun).where(SyncRun.status == SyncStatus.RUNNING))

    def latest(self) -> SyncRun | None:
        stmt = select(SyncRun).order_by(SyncRun.started_at.desc(), SyncRun.id.desc()).limit(1)
        return self.session.scalar(stmt)

    def latest_data_update(self) -> SyncRun | None:
        """Veriyi gerçekten yazan son sync (başarılı/kısmi); atlanan/başarısız sayılmaz."""
        stmt = (
            select(SyncRun)
            .where(SyncRun.status.in_((SyncStatus.SUCCESS, SyncStatus.PARTIAL)))
            .order_by(SyncRun.started_at.desc(), SyncRun.id.desc())
            .limit(1)
        )
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
        run.finished_at = func.now()  # tüm sync zamanları DB saatinden (sıralama tutarlı kalsın)
        run.requests_made = requests_made
        run.inserted = inserted
        run.updated = updated
        run.skipped = skipped
        run.error_message = error_message
        self.session.flush()
        self._load_timestamps(run)
        return run

    def _load_timestamps(self, run: SyncRun) -> None:
        # DB'de hesaplanan zamanları nesneye hemen yükle; oturum kapandıktan sonra da okunabilsin.
        self.session.refresh(run, ["started_at", "finished_at"])

    def fail_stale(self, older_than: timedelta) -> int:
        """Süreç çöktüğü için RUNNING'de asılı kalan kayıtları FAILED yapar (kilidi açar).

        Süre DB saatine göre ölçülür; uygulama ile DB saati farklı olsa da sonuç değişmez.
        """
        stmt = (
            update(SyncRun)
            .where(
                SyncRun.status == SyncStatus.RUNNING, SyncRun.started_at < func.now() - older_than
            )
            .values(
                status=SyncStatus.FAILED,
                finished_at=func.now(),
                error_message="Stale run: zaman aşımı nedeniyle sonlandırıldı",
            )
        )
        return self.session.execute(stmt).rowcount
