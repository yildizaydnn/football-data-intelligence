from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import FixtureServiceDep
from app.api.v1.common import SeasonQuery, error_responses
from app.core.enums import MatchStatus
from app.schemas.common import Paginated
from app.schemas.fixture import FixtureDetailOut, FixtureOut
from app.services.fixture_service import FixtureFilters

router = APIRouter(tags=["fixtures"])


@router.get(
    "/leagues/{league_id}/fixtures",
    response_model=Paginated[FixtureOut],
    responses=error_responses(404),
)
def list_fixtures(
    league_id: int,
    service: FixtureServiceDep,
    season: SeasonQuery = None,
    status: MatchStatus | None = None,
    team_id: int | None = None,
    date_from: Annotated[datetime | None, Query(description="Dahil, ISO 8601")] = None,
    date_to: Annotated[datetime | None, Query(description="Hariç, ISO 8601")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Paginated[FixtureOut]:
    filters = FixtureFilters(status=status, team_id=team_id, date_from=date_from, date_to=date_to)
    page = service.list_fixtures(league_id, season, filters, limit=limit, offset=offset)
    return Paginated[FixtureOut](
        items=[FixtureOut.model_validate(f) for f in page.items],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get(
    "/fixtures/{fixture_id}", response_model=FixtureDetailOut, responses=error_responses(404)
)
def get_fixture(fixture_id: int, service: FixtureServiceDep) -> FixtureDetailOut:
    return FixtureDetailOut.from_detail(service.get_fixture(fixture_id))
