from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.enums import MatchStatus
from app.models import League, Season, Team


@dataclass
class Seed:
    league: League
    season: Season
    home: Team
    away: Team

    def fixture_item(self, external_id: int = 1001, **overrides: Any) -> dict[str, Any]:
        """FixtureRepository.upsert'e verilecek, transformer çıktısı biçiminde bir kayıt."""
        item: dict[str, Any] = {
            "external_id": external_id,
            "season_id": self.season.id,
            "home_team_id": self.home.id,
            "away_team_id": self.away.id,
            "kickoff_at": datetime(2024, 9, 21, 17, 0, tzinfo=UTC),
            "status": MatchStatus.SCHEDULED,
            "status_raw": "NS",
            "home_goals": None,
            "away_goals": None,
            "round": "Regular Season - 6",
        }
        return item | overrides


@pytest.fixture
def seed(db_session: Session) -> Seed:
    league = League(external_id=203, name="Süper Lig", country="Turkey")
    season = Season(league=league, year=2024, is_current=True)
    home = Team(external_id=645, name="Galatasaray")
    away = Team(external_id=611, name="Fenerbahçe")
    db_session.add_all([season, home, away])
    db_session.flush()
    return Seed(league, season, home, away)
