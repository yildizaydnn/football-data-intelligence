from datetime import date, datetime

from pydantic import BaseModel

from app.core.enums import SyncStatus, SyncTrigger
from app.schemas.common import Schema


class SyncRequest(BaseModel):
    full: bool = False  # True: lig/sezon/takımlar da yenilenir (3 istek), False: sadece maçlar (1)


class SyncRunOut(Schema):
    id: int
    trigger: SyncTrigger
    status: SyncStatus
    started_at: datetime
    finished_at: datetime | None
    requests_made: int
    inserted: int
    updated: int
    skipped: int
    error_message: str | None


class SyncStateOut(Schema):
    running: SyncRunOut | None
    recent: list[SyncRunOut]


class SyncUsageOut(Schema):
    day: date
    requests_used: int
    daily_limit: int
    remaining: int
    provider_remaining: int | None
