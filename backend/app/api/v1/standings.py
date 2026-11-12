from fastapi import APIRouter

from app.api.deps import StandingsServiceDep
from app.api.v1.common import SeasonQuery, error_responses
from app.schemas.standings import StandingsOut

router = APIRouter(tags=["standings"])


@router.get(
    "/leagues/{league_id}/standings", response_model=StandingsOut, responses=error_responses(404)
)
def get_standings(
    league_id: int, service: StandingsServiceDep, season: SeasonQuery = None
) -> StandingsOut:
    return StandingsOut.from_standings(service.get_standings(league_id, season))
