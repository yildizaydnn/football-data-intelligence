from collections.abc import Iterator

import httpx
import pytest
import respx

from app.core.exceptions import ProviderError
from app.providers.llm.gemini import BASE_URL, GeminiGenerator

MODELS = ["model-a", "model-b"]


def _ok(text: str, *, thought: str | None = None, finish: str = "STOP") -> httpx.Response:
    parts = ([{"text": thought, "thought": True}] if thought else []) + [{"text": text}]
    return httpx.Response(
        200, json={"candidates": [{"content": {"parts": parts}, "finishReason": finish}]}
    )


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE_URL, assert_all_called=False) as router:
        yield router


@pytest.fixture
def generator() -> Iterator[GeminiGenerator]:
    with GeminiGenerator("key", MODELS) as g:
        yield g


def test_returns_text_and_model(api: respx.MockRouter, generator: GeminiGenerator) -> None:
    route = api.post("/models/model-a:generateContent").mock(return_value=_ok(" Analiz. "))

    result = generator.generate(system="s", prompt="p")

    assert (result.text, result.model) == ("Analiz.", "model-a")
    body = route.calls.last.request
    assert body.headers["x-goog-api-key"] == "key"
    assert b'"systemInstruction"' in body.content


def test_busy_model_falls_back_to_next(api: respx.MockRouter, generator: GeminiGenerator) -> None:
    api.post("/models/model-a:generateContent").respond(503)
    api.post("/models/model-b:generateContent").mock(return_value=_ok("Yedek"))

    assert generator.generate(system="s", prompt="p").model == "model-b"


def test_blocked_response_falls_back(api: respx.MockRouter, generator: GeminiGenerator) -> None:
    api.post("/models/model-a:generateContent").mock(return_value=_ok("x", finish="SAFETY"))
    api.post("/models/model-b:generateContent").mock(return_value=_ok("Temiz"))

    assert generator.generate(system="s", prompt="p").text == "Temiz"


def test_thought_parts_are_not_returned(api: respx.MockRouter, generator: GeminiGenerator) -> None:
    api.post("/models/model-a:generateContent").mock(
        return_value=_ok("Sonuç.", thought="iç düşünce")
    )

    assert generator.generate(system="s", prompt="p").text == "Sonuç."


def test_config_error_is_not_retried(api: respx.MockRouter, generator: GeminiGenerator) -> None:
    api.post("/models/model-a:generateContent").respond(
        400, json={"error": {"message": "API key not valid"}}
    )
    fallback = api.post("/models/model-b:generateContent")

    with pytest.raises(ProviderError, match="API key not valid"):
        generator.generate(system="s", prompt="p")
    assert not fallback.called


def test_all_models_busy(api: respx.MockRouter, generator: GeminiGenerator) -> None:
    api.post("/models/model-a:generateContent").respond(429)
    api.post("/models/model-b:generateContent").mock(side_effect=httpx.ReadTimeout("t"))

    with pytest.raises(ProviderError, match="yanıt vermiyor"):
        generator.generate(system="s", prompt="p")
