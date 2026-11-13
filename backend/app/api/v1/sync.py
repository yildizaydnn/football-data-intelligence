from fastapi import APIRouter, Depends

from app.api.deps import SyncServiceDep, SyncStatusServiceDep, require_sync_token
from app.api.v1.common import SeasonQuery, error_responses
from app.core.enums import SyncStatus
from app.schemas.sync import (
    ScheduledSyncOut,
    SyncRequest,
    SyncRunOut,
    SyncStateOut,
    SyncUsageOut,
    TrackedSyncOut,
)

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncRunOut, responses=error_responses(404, 409, 429))
def trigger_sync(service: SyncServiceDep, body: SyncRequest | None = None) -> SyncRunOut:
    """Arayüzden elle güncelleme (şifresiz). Yalnızca maçlar güncellenir.

    429: kota yetersiz ya da aynı lig/sezon için bekleme süresi dolmadı. 409: başka sync çalışıyor.
    Sync başladıktan sonraki hatalar 200 + status=failed olarak döner (kayıt oluşmuştur).
    """
    body = body or SyncRequest()
    return SyncRunOut.model_validate(service.run_manual(body.league_id, body.season))


@router.post(
    "/scheduled",
    response_model=ScheduledSyncOut,
    responses=error_responses(401),
    dependencies=[Depends(require_sync_token)],
)
def trigger_scheduled_sync(service: SyncServiceDep) -> ScheduledSyncOut:
    """Dış zamanlayıcı (GitHub Actions) için: takip edilen bütün ligler, X-Sync-Token ister.

    Uygulama içi zamanlayıcıyla aynı kurallar: bitmiş sezonlar istek atılmadan atlanır.
    """
    results = [
        TrackedSyncOut(
            league_external_id=r.league_external_id,
            run=SyncRunOut.model_validate(r.run) if r.run else None,
            error=r.error,
        )
        for r in service.run_tracked()
    ]
    failed = any(r.run is not None and r.run.status is SyncStatus.FAILED for r in results)
    return ScheduledSyncOut(results=results, failed=failed)


@router.get("/status", response_model=SyncStateOut, responses=error_responses(404))
def get_sync_status(service: SyncStatusServiceDep, league_id: int | None = None) -> SyncStateOut:
    """Çalışan sync ve son işlemler; `league_id` verilirse geçmiş o lige göre süzülür."""
    return SyncStateOut.model_validate(service.get_state(league_id=league_id))


@router.get("/usage", response_model=SyncUsageOut, responses=error_responses(404))
def get_sync_usage(
    service: SyncStatusServiceDep, league_id: int | None = None, season: SeasonQuery = None
) -> SyncUsageOut:
    """Kalan kota; `next_sync_cost` verilen lig/sezon için (boşsa varsayılan lig)."""
    return SyncUsageOut.model_validate(service.get_usage(league_id, season))
