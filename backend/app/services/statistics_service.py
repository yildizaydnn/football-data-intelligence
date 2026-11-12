"""Maç istatistikleri: isteğe bağlı (maç detayı açılınca) çekilir ve kalıcı saklanır.

Akış: DB'de varsa onu döndür → maç bitmemişse çekme → kota yedeğini koru → 1 istek at,
sakla ve "çekildi" damgasını vur (API veri sağlamasa bile; aynı maç tekrar istenmez).
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.enums import MatchStatus
from app.core.exceptions import NotFoundError, ProviderError, QuotaExceededError
from app.etl.transformers.statistics_transformer import StatisticsTransformer
from app.models import Fixture
from app.providers.base import MatchStatsProvider
from app.repositories.api_usage_repository import ApiUsageRepository
from app.repositories.fixture_repository import FixtureRepository
from app.repositories.statistics_repository import StatisticsRepository
from app.rules.engine import RuleEngine

logger = logging.getLogger(__name__)


class StatisticsAvailability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"  # sağlayıcı bu maç için veri vermiyor
    NOT_FINISHED = "not_finished"  # maç bitmeden çekilmez (değerler değişir)


@dataclass(frozen=True)
class StatLine:
    key: str
    home: float | None
    away: float | None


@dataclass(frozen=True)
class FixtureStatistics:
    fixture: Fixture
    availability: StatisticsAvailability
    fetched_at: datetime | None
    lines: list[StatLine]


class StatisticsService:
    def __init__(
        self,
        session: Session,
        settings: Settings,
        rules: RuleEngine,
        provider: MatchStatsProvider | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.rules = rules
        self.provider = provider
        self.fixtures = FixtureRepository(session)
        self.statistics = StatisticsRepository(session)
        self.api_usage = ApiUsageRepository(session)

    def get(self, fixture_id: int) -> FixtureStatistics:
        fixture = self.fixtures.get_with_teams(fixture_id)
        if fixture is None:
            raise NotFoundError(f"Maç bulunamadı: {fixture_id}")
        if fixture.statistics_fetched_at is None:
            if fixture.status is not MatchStatus.FINISHED:
                return FixtureStatistics(fixture, StatisticsAvailability.NOT_FINISHED, None, [])
            self._fetch(fixture)
        return self._stored(fixture)

    def _fetch(self, fixture: Fixture) -> None:
        if self.provider is None:
            raise RuntimeError("İstatistik çekmek için provider gerekli")
        limit = self.settings.api_football_daily_limit
        available = self.api_usage.remaining_budget(limit) - self.settings.statistics_quota_reserve
        if available < 1:
            raise QuotaExceededError(
                "Bugünkü kotanın kalanı otomatik güncellemelere ayrıldı; "
                "bu maçın istatistikleri yarın çekilebilir"
            )

        try:
            response = self.provider.get_fixture_statistics(fixture.external_id)
        except (ProviderError, QuotaExceededError) as exc:
            self.api_usage.record(exc.requests_made, daily_limit=limit)
            self.session.commit()
            raise
        self.api_usage.record(
            response.requests_made, daily_limit=limit, remaining=response.requests_remaining
        )

        league = fixture.season.league
        spec = self.rules.resolve(league.external_id, fixture.season.year).cleaning.statistics
        teams = {
            fixture.home_team.external_id: fixture.home_team_id,
            fixture.away_team.external_id: fixture.away_team_id,
        }
        result = StatisticsTransformer(fixture.id, teams, spec).transform_many(response.data)
        self.statistics.upsert([row for rows in result.items for row in rows])
        fixture.statistics_fetched_at = datetime.now(UTC)
        self.session.commit()
        logger.info("Maç %s istatistikleri çekildi (%d takım)", fixture.id, len(result.items))

    def _stored(self, fixture: Fixture) -> FixtureStatistics:
        rows = self.statistics.list_for_fixture(fixture.id)
        if not rows:
            return FixtureStatistics(
                fixture, StatisticsAvailability.UNAVAILABLE, fixture.statistics_fetched_at, []
            )
        values = {(row.team_id, row.key): row.value for row in rows}
        league = fixture.season.league
        order = self.rules.resolve(league.external_id, fixture.season.year).cleaning.statistics
        keys = [spec.key for spec in order.values() if any(k == spec.key for _, k in values)]
        lines = [
            StatLine(
                key,
                values.get((fixture.home_team_id, key)),
                values.get((fixture.away_team_id, key)),
            )
            for key in keys
        ]
        return FixtureStatistics(
            fixture, StatisticsAvailability.AVAILABLE, fixture.statistics_fetched_at, lines
        )
