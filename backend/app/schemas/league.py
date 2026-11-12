from datetime import date

from app.schemas.common import Schema


class LeagueOut(Schema):
    id: int
    external_id: int
    name: str
    country: str | None
    logo_url: str | None


class SeasonOut(Schema):
    id: int
    year: int
    start_date: date | None
    end_date: date | None
    is_current: bool
