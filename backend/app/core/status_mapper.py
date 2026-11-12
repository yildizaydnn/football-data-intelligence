"""API-Football durum kodları → MatchStatus.

Kaynak: https://www.api-football.com/documentation-v3#tag/Fixtures (status short kodları)
"""

from app.core.enums import MatchStatus

_STATUS_MAP: dict[str, MatchStatus] = {
    # Henüz başlamadı
    "TBD": MatchStatus.SCHEDULED,  # saat belirlenmedi
    "NS": MatchStatus.SCHEDULED,
    # Oynanıyor (devre arası, uzatma, penaltılar, kısa süreli duraklama dahil)
    "1H": MatchStatus.LIVE,
    "HT": MatchStatus.LIVE,
    "2H": MatchStatus.LIVE,
    "ET": MatchStatus.LIVE,
    "BT": MatchStatus.LIVE,
    "P": MatchStatus.LIVE,
    "SUSP": MatchStatus.LIVE,
    "INT": MatchStatus.LIVE,
    "LIVE": MatchStatus.LIVE,
    # Bitti (hükmen sonuçlar dahil; skor kesin)
    "FT": MatchStatus.FINISHED,
    "AET": MatchStatus.FINISHED,
    "PEN": MatchStatus.FINISHED,
    "AWD": MatchStatus.FINISHED,
    "WO": MatchStatus.FINISHED,
    # Ertelendi / iptal
    "PST": MatchStatus.POSTPONED,
    "CANC": MatchStatus.CANCELLED,
    "ABD": MatchStatus.CANCELLED,
}


class UnknownStatusError(ValueError):
    pass


def map_status(raw: str | None) -> MatchStatus:
    """Bilinmeyen kodda hata fırlatır; yanlış sınıflandırmaktansa kaydı atlamak daha güvenli."""
    if raw is None:
        raise UnknownStatusError("durum kodu yok")
    try:
        return _STATUS_MAP[raw.strip().upper()]
    except KeyError:
        raise UnknownStatusError(f"bilinmeyen durum kodu: {raw!r}") from None
