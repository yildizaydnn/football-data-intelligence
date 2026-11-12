from typing import Annotated, Any

from fastapi import Query

from app.schemas.common import ErrorResponse

SeasonQuery = Annotated[
    int | None, Query(ge=1900, le=2100, description="Sezon yılı; boşsa ligin güncel sezonu")
]


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI'de hata yanıtlarının da şemasıyla görünmesi için."""
    return {code: {"model": ErrorResponse} for code in status_codes}
