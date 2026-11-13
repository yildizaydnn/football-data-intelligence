"""OpenAI uyumlu /chat/completions API'leri (OpenRouter, DeepSeek, Groq...) ile metin üretimi.

Modeller sırayla denenir: meşgul (429/5xx), zaman aşımı, modelin bulunamaması/kotası (402/404)
ya da boş yanıtta sıradakine geçilir. Kimlik doğrulama hatası (401/403) diğer modellerde de
değişmeyeceği için hemen bildirilir.
"""

import logging
import re
from collections.abc import Mapping, Sequence
from typing import Any, Self

import httpx

from app.core.exceptions import ProviderError
from app.providers.llm.base import GeneratedText

logger = logging.getLogger(__name__)

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)


class OpenAICompatibleGenerator:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        models: Sequence[str],
        *,
        name: str,
        extra_headers: Mapping[str, str] | None = None,
        timeout: float = 30.0,
        max_tokens: int = 2048,  # "düşünen" modeller cevaptan önce bu bütçeden harcar
        temperature: float = 0.3,
    ) -> None:
        if not models:
            raise ValueError("En az bir model gerekli")
        self.name = name
        self._models = list(models)
        self._params = {"temperature": temperature, "max_tokens": max_tokens}
        self._http = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}", **(extra_headers or {})},
            timeout=timeout,
        )

    def generate(self, *, system: str, prompt: str) -> GeneratedText:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        failures: list[str] = []
        for model in self._models:
            try:
                response = self._http.post(
                    "/chat/completions", json={"model": model, "messages": messages, **self._params}
                )
            except httpx.TransportError as exc:
                failures.append(f"{model}: bağlantı/zaman aşımı")
                logger.warning("%s %s ulaşılamadı: %s", self.name, model, exc)
                continue
            if response.status_code in (401, 403):
                raise ProviderError(f"{self.name} anahtarı reddedildi: {_error_message(response)}")
            if response.status_code >= 400:
                failures.append(f"{model}: HTTP {response.status_code}")
                logger.warning("%s %s: HTTP %s", self.name, model, response.status_code)
                continue
            text = _extract_text(response.json())
            if text is None:
                failures.append(f"{model}: boş/engellenmiş yanıt")
                continue
            return GeneratedText(text=text, model=model)
        raise ProviderError(f"{self.name} yanıt vermedi ({'; '.join(failures)})")

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _extract_text(body: dict[str, Any]) -> str | None:
    choices = body.get("choices") or []
    if not choices or body.get("error"):
        return None
    choice = choices[0]
    if choice.get("finish_reason") in ("content_filter", "error"):
        return None
    content = (choice.get("message") or {}).get("content") or ""
    text = _THINK_BLOCK.sub("", content).strip()  # bazı modeller düşünceyi metne gömer
    return text or None


def _error_message(response: httpx.Response) -> str:
    try:
        return str(response.json()["error"]["message"])[:200]
    except (ValueError, KeyError, TypeError):
        return f"HTTP {response.status_code}"
