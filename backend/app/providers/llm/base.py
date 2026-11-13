from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeneratedText:
    text: str
    model: str  # yanıtı gerçekten üreten model (yedek modele düşülmüş olabilir)


class TextGenerator(Protocol):
    """Servislerin bağımlı olduğu LLM arayüzü. Somut zincir llm/factory.py'de kurulur."""

    def generate(self, *, system: str, prompt: str) -> GeneratedText: ...
