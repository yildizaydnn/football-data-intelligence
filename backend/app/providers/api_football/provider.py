from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.providers.api_football.client import ApiFootballClient, ApiResult
from app.providers.api_football.dto import FixtureDTO, LeagueDTO, TeamDTO, TeamStatisticsDTO
from app.providers.api_football.rate_limiter import shared_rate_limiter
from app.providers.base import ProviderResponse


class ApiFootballProvider:
    """FootballDataProvider'ın API-Football implementasyonu.

    Her metot tek bir endpoint çağırır; DB'ye dokunmaz, sadece veri ve kota bilgisi döner.
    """

    def __init__(self, client: ApiFootballClient) -> None:
        self._client = client

    def get_league(self, league_id: int) -> ProviderResponse[LeagueDTO]:
        return _to_response(self._client.get("/leagues", {"id": league_id}), LeagueDTO)

    def get_teams(self, league_id: int, season: int) -> ProviderResponse[TeamDTO]:
        result = self._client.get("/teams", {"league": league_id, "season": season})
        return _to_response(result, TeamDTO)

    def get_fixtures(
        self,
        league_id: int,
        season: int,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ProviderResponse[FixtureDTO]:
        params: dict[str, Any] = {"league": league_id, "season": season, "timezone": "UTC"}
        if (date_from is None) != (date_to is None):
            # API-Football 'from' ve 'to' parametrelerini yalnızca birlikte kabul eder.
            raise ValueError("date_from ve date_to birlikte verilmeli")
        if date_from and date_to:
            params |= {"from": date_from.isoformat(), "to": date_to.isoformat()}
        return _to_response(self._client.get("/fixtures", params), FixtureDTO)

    def get_fixture_statistics(self, fixture_id: int) -> ProviderResponse[TeamStatisticsDTO]:
        """Takım başına istatistikler; API veri sağlamıyorsa boş liste döner."""
        result = self._client.get("/fixtures/statistics", {"fixture": fixture_id})
        return _to_response(result, TeamStatisticsDTO)


def _to_response[T: BaseModel](result: ApiResult, dto: type[T]) -> ProviderResponse[T]:
    try:
        data = [dto.model_validate(item) for item in result.response]
    except ValidationError as exc:
        raise ProviderError(
            f"API-Football {dto.__name__} yanıtı beklenen biçimde değil: {exc.error_count()} hata",
            requests_made=result.requests_made,
        ) from exc
    return ProviderResponse(data, result.requests_remaining, result.requests_made)


@contextmanager
def build_api_football_provider(settings: Settings) -> Iterator[ApiFootballProvider]:
    """Ayarlardan provider kurar; çıkışta HTTP bağlantılarını kapatır."""
    with ApiFootballClient(
        settings.api_football_base_url,
        settings.api_football_key,
        timeout=settings.api_football_timeout_seconds,
        max_attempts=settings.api_football_max_attempts,
        limiter=shared_rate_limiter(settings.api_football_requests_per_minute),
    ) as client:
        yield ApiFootballProvider(client)
