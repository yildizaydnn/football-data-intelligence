from datetime import datetime

from app.schemas.common import Schema
from app.services.statistics_service import FixtureStatistics, StatisticsAvailability


class StatLineOut(Schema):
    key: str  # ör. shots_on_goal; sıra ve anahtarlar lig kural spec'inden
    home: float | None
    away: float | None


class FixtureStatisticsOut(Schema):
    fixture_id: int
    availability: StatisticsAvailability
    fetched_at: datetime | None
    lines: list[StatLineOut]

    @classmethod
    def from_statistics(cls, stats: FixtureStatistics) -> "FixtureStatisticsOut":
        return cls(
            fixture_id=stats.fixture.id,
            availability=stats.availability,
            fetched_at=stats.fetched_at,
            lines=[StatLineOut.model_validate(line) for line in stats.lines],
        )
