from pydantic import BaseModel, ConfigDict


class Schema(BaseModel):
    """Tüm yanıt şemalarının tabanı: ORM nesnelerinden ve dataclass'lardan okunabilir."""

    model_config = ConfigDict(from_attributes=True)


class Paginated[T](Schema):
    items: list[T]
    total: int
    limit: int
    offset: int


class ErrorDetail(Schema):
    code: str
    message: str
    details: list[dict] | None = None


class ErrorResponse(Schema):
    error: ErrorDetail
