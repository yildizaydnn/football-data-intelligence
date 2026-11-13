class AppError(Exception):
    """Bilinçli fırlatılan hataların tabanı. API katmanı bunları standart JSON'a çevirir."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ProviderError(AppError):
    """Dış veri kaynağına ulaşılamadı veya beklenmeyen bir yanıt döndü."""

    status_code = 502
    code = "provider_error"

    def __init__(self, message: str, *, requests_made: int = 0) -> None:
        super().__init__(message)
        # Başarısız da olsa atılan istekler kotadan düşer; sync bunları kaydedebilsin.
        self.requests_made = requests_made


class QuotaExceededError(AppError):
    """Günlük API istek bütçesi yetersiz."""

    status_code = 429
    code = "quota_exceeded"

    def __init__(self, message: str, *, requests_made: int = 0) -> None:
        super().__init__(message)
        self.requests_made = requests_made


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class SyncInProgressError(ConflictError):
    code = "sync_in_progress"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"


class AiNotConfiguredError(AppError):
    status_code = 503
    code = "ai_not_configured"
