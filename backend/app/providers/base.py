from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from app.providers.api_football.dto import FixtureDTO, LeagueDTO, TeamDTO, TeamStatisticsDTO


@dataclass(frozen=True)
class RejectedItem:
    """Yanıttaki biçimi bozuk kayıt (ör. `goals: null`); atlanır, gerisi işlenmeye devam eder."""

    record: str  # DTO adı, ör. "FixtureDTO"
    index: int  # ham yanıttaki sırası
    reason: str
    external_id: int | None = None


@dataclass(frozen=True)
class ProviderResponse[T]:
    data: list[T]
    requests_remaining: int | None  # header'dan okunan günlük kalan kota
    requests_made: int = 1  # retry'lar dahil gerçekten atılan istek sayısı (kotadan düşer)
    rejected: list[RejectedItem] = field(default_factory=list)


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


class MatchStatsProvider(Protocol):
    """Maç istatistikleri ayrı bir arayüz (ISP): sync tarafı bu metoda bağımlı olmaz."""

    def get_fixture_statistics(self, fixture_id: int) -> ProviderResponse[TeamStatisticsDTO]: ...
