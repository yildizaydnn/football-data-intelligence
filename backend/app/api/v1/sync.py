from fastapi import APIRouter

from app.api.deps import SyncServiceDep, SyncStatusServiceDep
from app.api.v1.common import error_responses
from app.core.enums import SyncTrigger
from app.schemas.sync import SyncRequest, SyncRunOut, SyncStateOut, SyncUsageOut

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncRunOut, responses=error_responses(409, 429))
def trigger_sync(service: SyncServiceDep, body: SyncRequest | None = None) -> SyncRunOut:
    """Elle senkronizasyon. Kota yetmezse 429, başka sync çalışıyorsa 409 döner.

    Sync başladıktan sonraki hatalar 200 + status=failed olarak döner (kayıt oluşmuştur).
    """
    run = service.run(SyncTrigger.MANUAL, full=body.full if body else False)
    return SyncRunOut.model_validate(run)


@router.get("/status", response_model=SyncStateOut)
def get_sync_status(service: SyncStatusServiceDep) -> SyncStateOut:
    return SyncStateOut.model_validate(service.get_state())


@router.get("/usage", response_model=SyncUsageOut)
def get_sync_usage(service: SyncStatusServiceDep) -> SyncUsageOut:
    return SyncUsageOut.model_validate(service.get_usage())
