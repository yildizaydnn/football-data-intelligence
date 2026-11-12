from fastapi import APIRouter

from app.api.deps import LeagueServiceDep, RulesServiceDep
from app.api.v1.common import SeasonQuery, error_responses
from app.schemas.league import LeagueOut, SeasonOut
from app.schemas.rules import RulesOut

router = APIRouter(prefix="/leagues", tags=["leagues"])


@router.get("", response_model=list[LeagueOut])
def list_leagues(service: LeagueServiceDep) -> list[LeagueOut]:
    return [LeagueOut.model_validate(league) for league in service.list_leagues()]


@router.get("/{league_id}", response_model=LeagueOut, responses=error_responses(404))
def get_league(league_id: int, service: LeagueServiceDep) -> LeagueOut:
    return LeagueOut.model_validate(service.get_league(league_id))


@router.get("/{league_id}/seasons", response_model=list[SeasonOut], responses=error_responses(404))
def list_seasons(league_id: int, service: LeagueServiceDep) -> list[SeasonOut]:
    return [SeasonOut.model_validate(season) for season in service.list_seasons(league_id)]


@router.get("/{league_id}/rules", response_model=RulesOut, responses=error_responses(404))
def get_league_rules(
    league_id: int, service: RulesServiceDep, season: SeasonQuery = None
) -> RulesOut:
    """Lig + sezon için geçerli kurallar: puanlar, sıralama kriterleri, tablo bölgeleri."""
    return RulesOut.from_context(service.get_rules(league_id, season))
