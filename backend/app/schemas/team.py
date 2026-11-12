from app.schemas.common import Schema


class TeamRef(Schema):
    """Başka yanıtların içine gömülen kısa takım bilgisi."""

    id: int
    name: str
    code: str | None
    logo_url: str | None


class TeamOut(TeamRef):
    external_id: int
    venue_name: str | None
