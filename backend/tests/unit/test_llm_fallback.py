from collections.abc import Iterator

import httpx
import pytest
import respx

from app.core.config import Settings
from app.core.exceptions import ProviderError
from app.providers.llm.base import GeneratedText
from app.providers.llm.chain import FallbackGenerator
from app.providers.llm.factory import build_text_generator
from app.providers.llm.openai_compatible import OpenAICompatibleGenerator

BASE = "https://router.test/api/v1"


def _completion(content: str, finish: str = "stop") -> httpx.Response:
    return httpx.Response(
        200, json={"choices": [{"message": {"content": content}, "finish_reason": finish}]}
    )


@pytest.fixture
def api() -> Iterator[respx.MockRouter]:
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def router_gen() -> Iterator[OpenAICompatibleGenerator]:
    with OpenAICompatibleGenerator(
        BASE, "key", ["m1", "m2"], name="Router", extra_headers={"X-Title": "FI"}
    ) as g:
        yield g


class TestOpenAICompatible:
    def test_sends_chat_request(self, api: respx.MockRouter, router_gen) -> None:
        route = api.post("/chat/completions").mock(return_value=_completion(" Analiz. "))

        result = router_gen.generate(system="sys", prompt="soru")

        assert (result.text, result.model) == ("Analiz.", "m1")
        request = route.calls.last.request
        assert request.headers["authorization"] == "Bearer key"
        assert request.headers["x-title"] == "FI"
        assert b'"role":"system"' in request.content.replace(b" ", b"")

    def test_rate_limited_or_missing_model_falls_back(self, api: respx.MockRouter, router_gen):
        api.post("/chat/completions").mock(side_effect=[httpx.Response(429), _completion("Yedek")])

        assert router_gen.generate(system="s", prompt="p").model == "m2"

    def test_think_block_is_stripped(self, api: respx.MockRouter, router_gen) -> None:
        api.post("/chat/completions").mock(
            return_value=_completion("<think>iç ses</think>\nSonuç.")
        )

        assert router_gen.generate(system="s", prompt="p").text == "Sonuç."

    def test_auth_error_stops_this_provider(self, api: respx.MockRouter, router_gen) -> None:
        route = api.post("/chat/completions").respond(401, json={"error": {"message": "bad key"}})

        with pytest.raises(ProviderError, match="bad key"):
            router_gen.generate(system="s", prompt="p")
        assert route.call_count == 1


class _Failing:
    def generate(self, *, system: str, prompt: str) -> GeneratedText:
        raise ProviderError("anahtar geçersiz")


class _Working:
    def generate(self, *, system: str, prompt: str) -> GeneratedText:
        return GeneratedText("tamam", "yedek-model")


def test_chain_moves_to_next_provider_on_any_provider_error() -> None:
    assert FallbackGenerator([_Failing(), _Working()]).generate(system="s", prompt="p").model == (
        "yedek-model"
    )


def test_chain_hides_internal_errors_from_users(caplog: pytest.LogCaptureFixture) -> None:
    with pytest.raises(ProviderError, match="yoğun") as exc_info:
        FallbackGenerator([_Failing(), _Failing()]).generate(system="s", prompt="p")

    assert "anahtar" not in exc_info.value.message  # iç ayrıntı kullanıcıya gitmez
    assert "anahtar geçersiz | anahtar geçersiz" in caplog.text  # ama log'da var


@pytest.mark.parametrize(
    ("keys", "enabled"),
    [({}, False), ({"gemini_api_key": "g"}, True), ({"openrouter_api_key": "o"}, True)],
)
def test_factory_builds_chain_from_available_keys(keys: dict, enabled: bool) -> None:
    settings = Settings(_env_file=None, **{"gemini_api_key": "", "openrouter_api_key": "", **keys})

    with build_text_generator(settings) as generator:
        assert (generator is not None) is enabled
