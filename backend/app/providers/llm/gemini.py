"""Google Gemini (generateContent REST API) ile metin üretimi.

Modeller sırayla denenir: biri yoğun (429/5xx) ya da zaman aşımındaysa sıradakine geçilir.
Yapılandırma hataları (400/401/403) diğer modellerde de değişmeyeceği için hemen bildirilir.
"""

import logging
from collections.abc import Sequence
from typing import Any, Self

import httpx

from app.core.exceptions import ProviderError
from app.providers.llm.base import GeneratedText

logger = logging.getLogger(__name__)

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiGenerator:
    def __init__(
        self,
        api_key: str,
        models: Sequence[str],
        *,
        timeout: float = 30.0,
        max_output_tokens: int = 2048,  # "düşünme" token'ları da bu sınırdan yer
        temperature: float = 0.3,
    ) -> None:
        if not models:
            raise ValueError("En az bir model gerekli")
        self._models = list(models)
        self._config = {"temperature": temperature, "maxOutputTokens": max_output_tokens}
        self._http = httpx.Client(
            base_url=BASE_URL, headers={"x-goog-api-key": api_key}, timeout=timeout
        )

    def generate(self, *, system: str, prompt: str) -> GeneratedText:
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": self._config,
        }
        failures: list[str] = []
        for model in self._models:
            try:
                response = self._http.post(f"/models/{model}:generateContent", json=body)
            except httpx.TransportError as exc:
                failures.append(f"{model}: bağlantı/zaman aşımı")
                logger.warning("Gemini %s ulaşılamadı: %s", model, exc)
                continue
            if response.status_code == 429 or response.status_code >= 500:
                failures.append(f"{model}: HTTP {response.status_code}")
                logger.warning("Gemini %s meşgul: HTTP %s", model, response.status_code)
                continue
            if response.status_code >= 400:
                raise ProviderError(f"AI servisi isteği reddetti: {_error_message(response)}")
            text = _extract_text(response.json())
            if text is None:
                failures.append(f"{model}: boş/engellenmiş yanıt")
                continue
            return GeneratedText(text=text, model=model)
        raise ProviderError(f"AI servisi şu an yanıt vermiyor ({'; '.join(failures)})")

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _extract_text(body: dict[str, Any]) -> str | None:
    candidates = body.get("candidates") or []
    if not candidates:
        return None
    candidate = candidates[0]
    if candidate.get("finishReason") not in (None, "STOP", "MAX_TOKENS"):
        return None  # SAFETY, RECITATION vb.
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts if not part.get("thought")).strip()
    return text or None


def _error_message(response: httpx.Response) -> str:
    try:
        return response.json()["error"]["message"][:200]
    except (ValueError, KeyError, TypeError):
        return f"HTTP {response.status_code}"
