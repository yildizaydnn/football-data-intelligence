import logging
from dataclasses import dataclass
from typing import Any, Self

import httpx
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential
from tenacity.wait import WaitBaseT

from app.core.exceptions import ProviderError, QuotaExceededError

logger = logging.getLogger(__name__)

REMAINING_HEADER = "x-ratelimit-requests-remaining"


@dataclass(frozen=True)
class ApiResult:
    response: list[Any]
    requests_remaining: int | None
    requests_made: int


class _RetryableError(Exception):
    """Tekrar denenmesi anlamlı hata: 429, 5xx, dakikalık rate limit."""


class ApiFootballClient:
    """API-Football'a HTTP erişimi. Retry, timeout ve kota header'ını yönetir; DB bilmez."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        timeout: float = 10.0,
        max_attempts: int = 3,
        wait: WaitBaseT | None = None,
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url,
            headers={"x-apisports-key": api_key},
            timeout=timeout,
        )
        self._max_attempts = max_attempts
        self._wait = wait or wait_exponential(multiplier=0.5, max=8)

    def get(self, path: str, params: dict[str, Any] | None = None) -> ApiResult:
        attempts = 0
        last_remaining: int | None = None

        def send() -> dict[str, Any]:
            nonlocal attempts, last_remaining
            attempts += 1
            try:
                response = self._http.get(path, params=params)
            except httpx.TransportError as exc:
                logger.warning("API-Football %s bağlantı hatası: %s", path, exc)
                raise _RetryableError(f"bağlantı hatası: {exc}") from exc

            last_remaining = _parse_int(response.headers.get(REMAINING_HEADER), last_remaining)

            if response.status_code == 429 or response.status_code >= 500:
                logger.warning("API-Football %s → HTTP %s", path, response.status_code)
                raise _RetryableError(f"HTTP {response.status_code}")
            if response.status_code >= 400:
                raise ProviderError(
                    f"API-Football HTTP {response.status_code}: {response.text[:200]}",
                    requests_made=attempts,
                )

            body = _json(response, attempts)
            errors = body.get("errors")
            if errors:
                self._raise_for_body_errors(errors, attempts)
            return body

        retrying = Retrying(
            stop=stop_after_attempt(self._max_attempts),
            wait=self._wait,
            retry=retry_if_exception_type(_RetryableError),
            reraise=True,
        )
        try:
            body = retrying(send)
        except _RetryableError as exc:
            raise ProviderError(
                f"API-Football {path} {attempts} denemede başarısız: {exc}",
                requests_made=attempts,
            ) from exc

        response_items = body.get("response")
        if not isinstance(response_items, list):
            raise ProviderError(
                "API-Football yanıtında 'response' listesi yok", requests_made=attempts
            )
        return ApiResult(response_items, last_remaining, attempts)

    @staticmethod
    def _raise_for_body_errors(errors: dict[str, str] | list[Any], attempts: int) -> None:
        # API-Football hataları çoğunlukla HTTP 200 + "errors" alanıyla döner.
        if isinstance(errors, dict):
            if "requests" in errors:
                raise QuotaExceededError(
                    f"API-Football günlük limit: {errors['requests']}", requests_made=attempts
                )
            if "rateLimit" in errors:
                raise _RetryableError(f"rate limit: {errors['rateLimit']}")
            message = "; ".join(f"{k}: {v}" for k, v in errors.items())
        else:
            message = "; ".join(map(str, errors))
        raise ProviderError(f"API-Football hata: {message}", requests_made=attempts)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _json(response: httpx.Response, attempts: int) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError as exc:
        raise ProviderError("API-Football geçersiz JSON döndü", requests_made=attempts) from exc
    if not isinstance(body, dict):
        raise ProviderError("API-Football beklenmeyen yanıt biçimi", requests_made=attempts)
    return body


def _parse_int(value: str | None, default: int | None) -> int | None:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default
