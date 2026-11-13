"""Ayarlardan LLM zinciri kurar: anahtarı olan sağlayıcılar sırayla (Gemini → OpenRouter)."""

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager

from app.core.config import Settings
from app.providers.llm.base import TextGenerator
from app.providers.llm.chain import FallbackGenerator
from app.providers.llm.gemini import GeminiGenerator
from app.providers.llm.openai_compatible import OpenAICompatibleGenerator


@contextmanager
def build_text_generator(settings: Settings) -> Iterator[TextGenerator | None]:
    """Hiç anahtar yoksa None verir: özellik kapalı, uygulamanın geri kalanı etkilenmez."""
    with ExitStack() as stack:
        generators: list[TextGenerator] = []
        if settings.gemini_api_key:
            generators.append(
                stack.enter_context(
                    GeminiGenerator(
                        settings.gemini_api_key,
                        settings.ai_models,
                        timeout=settings.ai_timeout_seconds,
                    )
                )
            )
        if settings.openrouter_api_key:
            generators.append(
                stack.enter_context(
                    OpenAICompatibleGenerator(
                        settings.openrouter_base_url,
                        settings.openrouter_api_key,
                        settings.openrouter_models,
                        name="OpenRouter",
                        extra_headers={"X-Title": "Football Intelligence"},
                        timeout=settings.ai_timeout_seconds,
                    )
                )
            )
        yield FallbackGenerator(generators) if generators else None
