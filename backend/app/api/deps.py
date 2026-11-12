"""Bağımlılık enjeksiyonu: somut sınıflar yalnızca burada seçilir (DIP).

Servisler FootballDataProvider arayüzüne bağımlıdır; ApiFootballProvider'ı bilen tek yer burası.
Testler get_session / get_provider / get_settings'i override ederek sahte bağımlılık verir.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.providers.api_football.client import ApiFootballClient
from app.providers.api_football.provider import ApiFootballProvider
from app.providers.base import FootballDataProvider
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.sync_repository import SyncRunRepository
from app.repositories.team_repository import TeamRepository
from app.services.fixture_service import FixtureService
from app.services.league_service import LeagueService
from app.services.overview_service import OverviewService
from app.services.standings_service import StandingsService
from app.services.sync_service import SyncService
from app.services.team_stats_service import TeamStatsService

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_provider(settings: SettingsDep) -> Iterator[FootballDataProvider]:
    with ApiFootballClient(
        settings.api_football_base_url,
        settings.api_football_key,
        timeout=settings.api_football_timeout_seconds,
        max_attempts=settings.api_football_max_attempts,
    ) as client:
        yield ApiFootballProvider(client)


ProviderDep = Annotated[FootballDataProvider, Depends(get_provider)]


def get_league_service(session: SessionDep) -> LeagueService:
    return LeagueService(LeagueRepository(session), SeasonRepository(session))


LeagueServiceDep = Annotated[LeagueService, Depends(get_league_service)]


def get_fixture_service(session: SessionDep, leagues: LeagueServiceDep) -> FixtureService:
    return FixtureService(FixtureRepository(session), leagues)


def get_standings_service(session: SessionDep, leagues: LeagueServiceDep) -> StandingsService:
    return StandingsService(FixtureRepository(session), TeamRepository(session), leagues)


def get_team_stats_service(session: SessionDep, leagues: LeagueServiceDep) -> TeamStatsService:
    return TeamStatsService(FixtureRepository(session), TeamRepository(session), leagues)


StandingsServiceDep = Annotated[StandingsService, Depends(get_standings_service)]


def get_overview_service(
    session: SessionDep, leagues: LeagueServiceDep, standings: StandingsServiceDep
) -> OverviewService:
    return OverviewService(
        FixtureRepository(session), SyncRunRepository(session), leagues, standings
    )


def get_sync_service(
    session: SessionDep, provider: ProviderDep, settings: SettingsDep
) -> SyncService:
    return SyncService(session, settings, provider)


def get_sync_status_service(session: SessionDep, settings: SettingsDep) -> SyncService:
    """Sadece okuma yapan sync uçları için: provider (HTTP client) kurulmaz."""
    return SyncService(session, settings)


FixtureServiceDep = Annotated[FixtureService, Depends(get_fixture_service)]
TeamStatsServiceDep = Annotated[TeamStatsService, Depends(get_team_stats_service)]
OverviewServiceDep = Annotated[OverviewService, Depends(get_overview_service)]
SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]
SyncStatusServiceDep = Annotated[SyncService, Depends(get_sync_status_service)]
