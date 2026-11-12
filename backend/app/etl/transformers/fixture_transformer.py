from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from app.core.enums import MatchStatus
from app.core.status_mapper import UnknownStatusError, map_status
from app.etl.base import BaseTransformer, TransformError, require
from app.providers.api_football.dto import FixtureDTO

# Bu durumlarda skor anlamsızdır; API bazen 0-0 gönderse bile saklanmaz.
_NO_SCORE_STATUSES = {MatchStatus.SCHEDULED, MatchStatus.POSTPONED, MatchStatus.CANCELLED}


class FixtureTransformer(BaseTransformer[FixtureDTO, dict[str, Any]]):
    """FixtureDTO → fixtures tablosu satırı.

    Takım FK'larını çözebilmek için sezonun iç id'si ve takım external_id → id eşlemesi,
    durum kodlarını yorumlamak için ligin kural spec'indeki eşleme tablosu verilir.
    """

    def __init__(
        self,
        season_id: int,
        team_ids: Mapping[int, int],
        status_map: Mapping[str, MatchStatus],
    ) -> None:
        self.season_id = season_id
        self.team_ids = team_ids
        self.status_map = status_map

    def transform(self, item: FixtureDTO) -> dict[str, Any]:
        external_id = require(item.fixture.id, "fixture.id")
        status_raw = require(item.fixture.status.short, "fixture.status.short").strip().upper()
        try:
            status = map_status(status_raw, self.status_map)
        except UnknownStatusError as exc:
            raise TransformError(str(exc)) from exc

        home_team_id = self._team_id(item.teams.home.id, "home")
        away_team_id = self._team_id(item.teams.away.id, "away")
        if home_team_id == away_team_id:
            raise TransformError("ev sahibi ve deplasman aynı takım")

        home_goals, away_goals = self._goals(item, status)

        return {
            "external_id": external_id,
            "season_id": self.season_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "kickoff_at": _parse_kickoff(item),
            "status": status,
            "status_raw": status_raw,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "round": (item.league.round or "").strip() or None,
        }

    def external_id_of(self, item: FixtureDTO) -> int | None:
        return item.fixture.id

    def _team_id(self, external_id: int | None, side: str) -> int:
        external_id = require(external_id, f"teams.{side}.id")
        try:
            return self.team_ids[external_id]
        except KeyError:
            raise TransformError(f"{side} takımı ({external_id}) veritabanında yok") from None

    @staticmethod
    def _goals(item: FixtureDTO, status: MatchStatus) -> tuple[int | None, int | None]:
        if status in _NO_SCORE_STATUSES:
            return None, None
        home, away = item.goals.home, item.goals.away
        if (home is None) != (away is None):
            raise TransformError("skorun yalnızca bir tarafı var")
        if home is not None and away is not None and (home < 0 or away < 0):
            raise TransformError("negatif skor")
        if status is MatchStatus.FINISHED and home is None:
            raise TransformError("bitmiş maçın skoru yok")
        return home, away


def _parse_kickoff(item: FixtureDTO) -> datetime:
    if item.fixture.date:
        try:
            kickoff = datetime.fromisoformat(item.fixture.date)
        except ValueError as exc:
            raise TransformError(f"geçersiz tarih: {item.fixture.date!r}") from exc
        # Saat dilimi yoksa API'ye timezone=UTC ile sorulduğu için UTC kabul edilir.
        return (kickoff if kickoff.tzinfo else kickoff.replace(tzinfo=UTC)).astimezone(UTC)
    if item.fixture.timestamp is not None:
        return datetime.fromtimestamp(item.fixture.timestamp, tz=UTC)
    raise TransformError("fixture.date eksik")
