from fastapi import APIRouter, Depends

from app.api.deps import SyncServiceDep, SyncStatusServiceDep, require_sync_token
from app.api.v1.common import SeasonQuery, error_responses
from app.schemas.sync import SyncRequest, SyncRunOut, SyncStateOut, SyncUsageOut

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "",
    response_model=SyncRunOut,
    responses=error_responses(401, 409, 429),
    dependencies=[Depends(require_sync_token)],
)
def trigger_sync(service: SyncServiceDep, body: SyncRequest | None = None) -> SyncRunOut:
    """Elle senkronizasyon. Kota yetmezse 429, başka sync çalışıyorsa 409 döner.

    Sync başladıktan sonraki hatalar 200 + status=failed olarak döner (kayıt oluşmuştur).
    """
    body = body or SyncRequest()
    run = service.run_manual(body.league_id, body.season, full=body.full)
    return SyncRunOut.model_validate(run)


@router.get("/status", response_model=SyncStateOut)
def get_sync_status(service: SyncStatusServiceDep) -> SyncStateOut:
    return SyncStateOut.model_validate(service.get_state())


@router.get("/usage", response_model=SyncUsageOut, responses=error_responses(404))
def get_sync_usage(
    service: SyncStatusServiceDep, league_id: int | None = None, season: SeasonQuery = None
) -> SyncUsageOut:
    """Kalan kota; `next_sync_cost` verilen lig/sezon için (boşsa varsayılan lig)."""
    return SyncUsageOut.model_validate(service.get_usage(league_id, season))
