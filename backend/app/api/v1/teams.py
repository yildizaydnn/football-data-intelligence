from fastapi import APIRouter

from app.api.deps import TeamStatsServiceDep
from app.api.v1.common import SeasonQuery, error_responses
from app.schemas.team import TeamOut
from app.schemas.team_stats import TeamStatsOut

router = APIRouter(prefix="/leagues/{league_id}/teams", tags=["teams"])


@router.get("", response_model=list[TeamOut], responses=error_responses(404))
def list_teams(
    league_id: int, service: TeamStatsServiceDep, season: SeasonQuery = None
) -> list[TeamOut]:
    return [TeamOut.model_validate(team) for team in service.list_teams(league_id, season)]


@router.get("/{team_id}/stats", response_model=TeamStatsOut, responses=error_responses(404))
def get_team_stats(
    league_id: int, team_id: int, service: TeamStatsServiceDep, season: SeasonQuery = None
) -> TeamStatsOut:
    return TeamStatsOut.from_stats(service.get_team_stats(league_id, team_id, season))
