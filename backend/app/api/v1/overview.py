from fastapi import APIRouter

from app.api.deps import OverviewServiceDep
from app.api.v1.common import SeasonQuery, error_responses
from app.schemas.overview import OverviewOut

router = APIRouter(tags=["overview"])


@router.get(
    "/leagues/{league_id}/overview", response_model=OverviewOut, responses=error_responses(404)
)
def get_overview(
    league_id: int, service: OverviewServiceDep, season: SeasonQuery = None
) -> OverviewOut:
    return OverviewOut.from_overview(service.get_overview(league_id, season))
