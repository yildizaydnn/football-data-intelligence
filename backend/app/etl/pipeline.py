import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from app.core.exceptions import NotFoundError, ProviderError, QuotaExceededError
from app.etl.base import SkippedRecord
from app.etl.transformers.fixture_transformer import FixtureTransformer
from app.etl.transformers.league_transformer import LeagueTransformer, SeasonTransformer
from app.etl.transformers.team_transformer import TeamTransformer
from app.providers.base import FootballDataProvider, ProviderResponse
from app.repositories.base import UpsertResult
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.league_repository import LeagueRepository, SeasonRepository
from app.repositories.team_repository import TeamRepository

logger = logging.getLogger(__name__)

REFERENCE_REQUESTS = 2  # /leagues + /teams
FIXTURE_REQUESTS = 1  # /fixtures


@dataclass
class PipelineResult:
    upsert: UpsertResult = field(default_factory=UpsertResult)
    skipped: list[SkippedRecord] = field(default_factory=list)


@dataclass
class Repositories:
    leagues: LeagueRepository
    seasons: SeasonRepository
    teams: TeamRepository
    fixtures: FixtureRepository


class SyncPipeline:
    """extract → transform → load. Kota, kilit ve commit kararları sync_service'e aittir.

    `requests_made` / `requests_remaining` hata durumunda da güncel kalır; servis
    pipeline patlasa bile harcanan isteği kotaya yazabilir.
    """

    def __init__(self, provider: FootballDataProvider, repos: Repositories) -> None:
        self.provider = provider
        self.repos = repos
        self.requests_made = 0
        self.requests_remaining: int | None = None

    def needs_reference(self, league_external_id: int, season_year: int) -> bool:
        """Lig/sezon DB'de yoksa fixture'lardan önce referans veri çekilmeli."""
        league = self.repos.leagues.get_by_external_id(league_external_id)
        return league is None or self.repos.seasons.get_by_year(league.id, season_year) is None

    def estimate_requests(self, league_external_id: int, season_year: int, *, full: bool) -> int:
        reference = full or self.needs_reference(league_external_id, season_year)
        return FIXTURE_REQUESTS + (REFERENCE_REQUESTS if reference else 0)

    def run(
        self,
        league_external_id: int,
        season_year: int,
        *,
        full: bool = False,
        sync_run_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> PipelineResult:
        result = PipelineResult()
        if full or self.needs_reference(league_external_id, season_year):
            self._load_reference(league_external_id, season_year, result)
        self._load_fixtures(
            league_external_id, season_year, result, sync_run_id, date_from, date_to
        )
        logger.info(
            "Pipeline bitti: lig=%s sezon=%s %s skipped=%d istek=%d",
            league_external_id,
            season_year,
            result.upsert,
            len(result.skipped),
            self.requests_made,
        )
        return result

    def _load_reference(
        self, league_external_id: int, season_year: int, result: PipelineResult
    ) -> None:
        league_resp = self._call(lambda: self.provider.get_league(league_external_id))
        leagues = LeagueTransformer().transform_many(league_resp.data)
        result.skipped += leagues.skipped
        result.upsert += self.repos.leagues.upsert(leagues.items)

        league = self.repos.leagues.get_by_external_id(league_external_id)
        if league is None:
            raise NotFoundError(f"Lig {league_external_id} sağlayıcıda bulunamadı")

        season_infos = [s for dto in league_resp.data for s in dto.seasons]
        seasons = SeasonTransformer(league.id).transform_many(season_infos)
        result.skipped += seasons.skipped
        result.upsert += self.repos.seasons.upsert(seasons.items)

        teams_resp = self._call(lambda: self.provider.get_teams(league_external_id, season_year))
        teams = TeamTransformer().transform_many(teams_resp.data)
        result.skipped += teams.skipped
        result.upsert += self.repos.teams.upsert(teams.items)

    def _load_fixtures(
        self,
        league_external_id: int,
        season_year: int,
        result: PipelineResult,
        sync_run_id: int | None,
        date_from: date | None,
        date_to: date | None,
    ) -> None:
        league = self.repos.leagues.get_by_external_id(league_external_id)
        season = league and self.repos.seasons.get_by_year(league.id, season_year)
        if not season:
            raise NotFoundError(f"Sezon {season_year} (lig {league_external_id}) bulunamadı")

        response = self._call(
            lambda: self.provider.get_fixtures(
                league_external_id, season_year, date_from=date_from, date_to=date_to
            )
        )
        team_external_ids = [
            team_id
            for dto in response.data
            for team_id in (dto.teams.home.id, dto.teams.away.id)
            if team_id is not None
        ]
        transformer = FixtureTransformer(season.id, self.repos.teams.id_map(team_external_ids))
        fixtures = transformer.transform_many(response.data)
        result.skipped += fixtures.skipped
        result.upsert += self.repos.fixtures.upsert_with_changes(fixtures.items, sync_run_id)

    def _call[T](self, fetch: Callable[[], ProviderResponse[T]]) -> ProviderResponse[T]:
        try:
            response = fetch()
        except (ProviderError, QuotaExceededError) as exc:
            self.requests_made += exc.requests_made
            raise
        self.requests_made += response.requests_made
        if response.requests_remaining is not None:
            self.requests_remaining = response.requests_remaining
        return response
