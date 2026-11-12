from datetime import datetime

from app.core.enums import MatchStatus
from app.schemas.common import Schema
from app.schemas.team import TeamRef
from app.services.fixture_service import FixtureDetail


class FixtureOut(Schema):
    id: int
    external_id: int
    kickoff_at: datetime
    status: MatchStatus
    status_raw: str
    round: str | None
    home_team: TeamRef
    away_team: TeamRef
    home_goals: int | None
    away_goals: int | None


class FixtureChangeOut(Schema):
    field: str
    old_value: str | None
    new_value: str | None
    changed_at: datetime
    sync_run_id: int | None


class FixtureDetailOut(FixtureOut):
    changes: list[FixtureChangeOut]

    @classmethod
    def from_detail(cls, detail: FixtureDetail) -> "FixtureDetailOut":
        base = FixtureOut.model_validate(detail.fixture).model_dump()
        return cls(**base, changes=detail.changes)
