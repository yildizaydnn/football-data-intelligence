from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeneratedText:
    text: str
    model: str  # yanıtı gerçekten üreten model (yedek modele düşülmüş olabilir)


class TextGenerator(Protocol):
    """Servislerin bağımlı olduğu LLM arayüzü. Somut sınıf (GeminiGenerator) deps.py'de bağlanır."""

    def generate(self, *, system: str, prompt: str) -> GeneratedText: ...
