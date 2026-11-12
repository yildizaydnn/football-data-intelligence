from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.models import ApiUsage
from app.repositories.base import BaseRepository


def utc_today() -> date:
    # API-Football günlük kotayı UTC gece yarısında sıfırlar.
    return datetime.now(UTC).date()


class ApiUsageRepository(BaseRepository[ApiUsage]):
    model = ApiUsage

    def get_for_day(self, day: date | None = None) -> ApiUsage | None:
        return self.session.scalar(select(ApiUsage).where(ApiUsage.date == (day or utc_today())))

    def record(
        self,
        requests: int,
        *,
        daily_limit: int,
        remaining: int | None = None,
        day: date | None = None,
    ) -> ApiUsage:
        """Günün sayacını atomik olarak artırır; API'nin bildirdiği kalan kotayı saklar."""
        stmt = insert(ApiUsage).values(
            date=day or utc_today(),
            requests_used=requests,
            daily_limit=daily_limit,
            remaining=remaining,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["date"],
            set_={
                "requests_used": ApiUsage.requests_used + stmt.excluded.requests_used,
                "daily_limit": stmt.excluded.daily_limit,
                "remaining": func.coalesce(stmt.excluded.remaining, ApiUsage.remaining),
                "updated_at": func.now(),
            },
        ).returning(ApiUsage)
        usage = self.session.scalars(stmt, execution_options={"populate_existing": True}).one()
        return usage

    def remaining_budget(self, daily_limit: int, day: date | None = None) -> int:
        """Bugün kalan istek hakkı.

        Kendi sayacımız ile API'nin header'da bildirdiği değerden küçük olanı esas alınır;
        API anahtarı başka bir yerde de kullanılmışsa header daha doğrudur.
        """
        usage = self.get_for_day(day)
        if usage is None:
            return daily_limit
        own = usage.daily_limit - usage.requests_used
        candidates = [own] if usage.remaining is None else [own, usage.remaining]
        return max(0, min(candidates))
