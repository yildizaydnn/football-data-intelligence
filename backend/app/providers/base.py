from dataclasses import dataclass
from datetime import date
from typing import Protocol

from app.providers.api_football.dto import FixtureDTO, LeagueDTO, TeamDTO


@dataclass(frozen=True)
class ProviderResponse[T]:
    data: list[T]
    requests_remaining: int | None  # header'dan okunan günlük kalan kota
    requests_made: int = 1  # retry'lar dahil gerçekten atılan istek sayısı (kotadan düşer)


class FootballDataProvider(Protocol):
    """Servislerin bağımlı olduğu arayüz. Somut sınıf (ApiFootballProvider) deps.py'de bağlanır."""

    def get_league(self, league_id: int) -> ProviderResponse[LeagueDTO]: ...

    def get_teams(self, league_id: int, season: int) -> ProviderResponse[TeamDTO]: ...

    def get_fixtures(
        self,
        league_id: int,
        season: int,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> ProviderResponse[FixtureDTO]: ...
