"""Sağlayıcı durum kodu → MatchStatus.

Eşleme tablosu kural katmanından (rules spec → cleaning.status_map) gelir; bir lig ya da
sezon belirli kodları farklı yorumlayabilir. Burada yalnızca normalize + arama yapılır.
"""

from collections.abc import Mapping

from app.core.enums import MatchStatus


class UnknownStatusError(ValueError):
    pass


def map_status(raw: str | None, mapping: Mapping[str, MatchStatus]) -> MatchStatus:
    """Bilinmeyen kodda hata fırlatır; yanlış sınıflandırmaktansa kaydı atlamak daha güvenli."""
    if raw is None or not raw.strip():
        raise UnknownStatusError("durum kodu yok")
    try:
        return mapping[raw.strip().upper()]
    except KeyError:
        raise UnknownStatusError(f"bilinmeyen durum kodu: {raw!r}") from None
