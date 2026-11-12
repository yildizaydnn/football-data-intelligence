import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class TransformError(ValueError):
    """Kayıt geçersiz; atlanmalı."""


@dataclass(frozen=True)
class SkippedRecord:
    transformer: str
    index: int
    reason: str
    external_id: int | None = None


@dataclass
class TransformResult[Out]:
    items: list[Out] = field(default_factory=list)
    skipped: list[SkippedRecord] = field(default_factory=list)


class BaseTransformer[In, Out](ABC):
    """Tek kaydın dönüşümünü alt sınıf yazar; toplu işleme ve hata toleransı burada."""

    def transform_many(self, items: Sequence[In]) -> TransformResult[Out]:
        result: TransformResult[Out] = TransformResult()
        for index, item in enumerate(items):
            try:
                result.items.append(self.transform(item))
            except TransformError as exc:
                self._skip(result, index, item, str(exc))
            except Exception as exc:  # beklenmeyen veri: tek kayıt yüzünden sync çökmesin
                logger.exception("%s: kayıt %d dönüştürülemedi", type(self).__name__, index)
                self._skip(result, index, item, f"beklenmeyen hata: {exc!r}")
        return result

    @abstractmethod
    def transform(self, item: In) -> Out: ...

    def external_id_of(self, item: In) -> int | None:
        """Loglarda kaydı tanımlamak için; alt sınıf isterse override eder."""
        return None

    def _skip(self, result: TransformResult[Out], index: int, item: In, reason: str) -> None:
        external_id = self.external_id_of(item)
        logger.warning(
            "%s: kayıt atlandı (index=%d, external_id=%s): %s",
            type(self).__name__,
            index,
            external_id,
            reason,
        )
        result.skipped.append(SkippedRecord(type(self).__name__, index, reason, external_id))


def require[T](value: T | None, name: str) -> T:
    if value is None or (isinstance(value, str) and not value.strip()):
        raise TransformError(f"{name} eksik")
    return value
