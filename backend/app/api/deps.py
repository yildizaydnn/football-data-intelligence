"""Bağımlılık enjeksiyonu: somut sınıflar yalnızca burada seçilir (DIP).

Servisler FootballDataProvider arayüzüne bağımlıdır; ApiFootballProvider'ı bilen tek yer burası.
Testler get_session / get_provider / get_settings'i override ederek sahte bağımlılık verir.
"""

import secrets
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.exceptions import UnauthorizedError
from app.providers.api_football.provider import build_api_football_provider
from app.providers.base import FootballDataProvider
from app.providers.llm.base import TextGenerator
from app.providers.llm.factory import build_text_generator
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.sync_repository import SyncRunRepository
from app.repositories.team_repository import TeamRepository
from app.rules.engine import RuleEngine, get_rule_engine
from app.services.fixture_service import FixtureService
from app.services.insight_service import InsightService
from app.services.league_service import LeagueService
from app.services.overview_service import OverviewService
from app.services.rules_service import RulesService
from app.services.standings_service import StandingsService
from app.services.statistics_service import StatisticsService
from app.services.sync_service import SyncService
from app.services.team_stats_service import TeamStatsService

SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_provider(settings: SettingsDep) -> Iterator[FootballDataProvider]:
    with build_api_football_provider(settings) as provider:
        yield provider


ProviderDep = Annotated[FootballDataProvider, Depends(get_provider)]
RuleEngineDep = Annotated[RuleEngine, Depends(get_rule_engine)]


def require_sync_token(
    settings: SettingsDep, x_sync_token: Annotated[str | None, Header()] = None
) -> None:
    """SYNC_API_TOKEN tanımlıysa sync tetikleme yetkisi ister; boşsa (yerel geliştirme) açık."""
    expected = settings.sync_api_token
    if expected and not secrets.compare_digest(x_sync_token or "", expected):
        raise UnauthorizedError("Geçersiz veya eksik X-Sync-Token")


def get_league_service(session: SessionDep) -> LeagueService:
    return LeagueService(LeagueRepository(session), SeasonRepository(session))


LeagueServiceDep = Annotated[LeagueService, Depends(get_league_service)]


def get_rules_service(leagues: LeagueServiceDep, rules: RuleEngineDep) -> RulesService:
    return RulesService(leagues, rules)


RulesServiceDep = Annotated[RulesService, Depends(get_rules_service)]


def get_fixture_service(session: SessionDep, leagues: LeagueServiceDep) -> FixtureService:
    return FixtureService(FixtureRepository(session), leagues)


def get_standings_service(
    session: SessionDep, leagues: LeagueServiceDep, rules: RuleEngineDep
) -> StandingsService:
    return StandingsService(FixtureRepository(session), TeamRepository(session), leagues, rules)


def get_team_stats_service(
    session: SessionDep, leagues: LeagueServiceDep, rules: RuleEngineDep
) -> TeamStatsService:
    return TeamStatsService(FixtureRepository(session), TeamRepository(session), leagues, rules)


StandingsServiceDep = Annotated[StandingsService, Depends(get_standings_service)]


def get_overview_service(
    session: SessionDep,
    leagues: LeagueServiceDep,
    standings: StandingsServiceDep,
    rules: RuleEngineDep,
) -> OverviewService:
    return OverviewService(
        FixtureRepository(session), SyncRunRepository(session), leagues, standings, rules
    )


def get_sync_service(
    session: SessionDep, provider: ProviderDep, settings: SettingsDep, rules: RuleEngineDep
) -> SyncService:
    return SyncService(session, settings, provider, rules)


def get_sync_status_service(session: SessionDep, settings: SettingsDep) -> SyncService:
    """Sadece okuma yapan sync uçları için: provider (HTTP client) kurulmaz."""
    return SyncService(session, settings)


def get_statistics_service(
    session: SessionDep, settings: SettingsDep, rules: RuleEngineDep, provider: ProviderDep
) -> StatisticsService:
    return StatisticsService(session, settings, rules, provider)


def get_text_generator(settings: SettingsDep) -> Iterator[TextGenerator | None]:
    with build_text_generator(settings) as generator:
        yield generator


def get_insight_service(
    session: SessionDep,
    settings: SettingsDep,
    leagues: LeagueServiceDep,
    rules: RuleEngineDep,
    generator: Annotated[TextGenerator | None, Depends(get_text_generator)],
) -> InsightService:
    return InsightService(session, settings, leagues, rules, generator)


InsightServiceDep = Annotated[InsightService, Depends(get_insight_service)]
FixtureServiceDep = Annotated[FixtureService, Depends(get_fixture_service)]
StatisticsServiceDep = Annotated[StatisticsService, Depends(get_statistics_service)]
TeamStatsServiceDep = Annotated[TeamStatsService, Depends(get_team_stats_service)]
OverviewServiceDep = Annotated[OverviewService, Depends(get_overview_service)]
SyncServiceDep = Annotated[SyncService, Depends(get_sync_service)]
SyncStatusServiceDep = Annotated[SyncService, Depends(get_sync_status_service)]
