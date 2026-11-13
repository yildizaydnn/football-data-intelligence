from datetime import date, datetime

from pydantic import BaseModel

from app.core.enums import SyncStatus, SyncTrigger
from app.schemas.common import Schema


class SyncRequest(BaseModel):
    league_id: int | None = None  # boşsa varsayılan lig (DEFAULT_LEAGUE_ID)
    season: int | None = None  # boşsa varsayılan sezon


class SyncRunOut(Schema):
    id: int
    trigger: SyncTrigger
    status: SyncStatus
    league_external_id: int | None
    season: int | None
    started_at: datetime
    finished_at: datetime | None
    requests_made: int
    inserted: int
    updated: int
    skipped: int
    error_message: str | None


class TrackedSyncOut(Schema):
    league_external_id: int
    run: SyncRunOut | None
    error: str | None  # sync başlamadan reddedildiyse nedeni (kota yetersiz, başka sync çalışıyor)


class ScheduledSyncOut(Schema):
    results: list[TrackedSyncOut]
    # Başlayıp başarısız olan sync var mı; dış cron bunu hata sayar.
    failed: bool


class SyncScheduleOut(Schema):
    enabled: bool
    cron: str
    next_run_at: datetime | None


class SyncStateOut(Schema):
    running: SyncRunOut | None
    recent: list[SyncRunOut]
    schedule: SyncScheduleOut


class SyncUsageOut(Schema):
    day: date
    requests_used: int
    daily_limit: int
    remaining: int
    provider_remaining: int | None
    next_sync_cost: int
    can_sync: bool
