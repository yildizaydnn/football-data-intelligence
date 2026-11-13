import logging
from collections.abc import Sequence

from app.core.exceptions import ProviderError
from app.providers.llm.base import GeneratedText, TextGenerator

logger = logging.getLogger(__name__)


class FallbackGenerator:
    """Sağlayıcıları sırayla dener (ör. Gemini → OpenRouter).

    Bir sağlayıcının her türlü hatası (yoğunluk, kota, hatta geçersiz anahtar) bir sonrakine
    geçiş sebebidir: tek bir servisin sorunu özelliği düşürmesin.
    """

    def __init__(self, generators: Sequence[TextGenerator]) -> None:
        if not generators:
            raise ValueError("En az bir sağlayıcı gerekli")
        self._generators = list(generators)

    def generate(self, *, system: str, prompt: str) -> GeneratedText:
        errors: list[str] = []
        for generator in self._generators:
            try:
                return generator.generate(system=system, prompt=prompt)
            except ProviderError as exc:
                logger.warning("AI sağlayıcısı başarısız, sıradakine geçiliyor: %s", exc.message)
                errors.append(exc.message)
        # Ayrıntılar log'da; kullanıcıya iç hata metinleri gösterilmez.
        logger.error("Tüm AI sağlayıcıları başarısız: %s", " | ".join(errors))
        raise ProviderError("AI servisleri şu an yoğun; lütfen biraz sonra tekrar deneyin")
