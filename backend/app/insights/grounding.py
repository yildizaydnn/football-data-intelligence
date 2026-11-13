"""Üretilen metindeki sayıların veriye dayanıp dayanmadığını kontrol eder (saf).

Kabul edilenler: verideki tüm sayılar (tam sayı, 1-2 ondalık, yüzde), iki takımın aynı
metriği arasındaki farklar ve sezon yılları. Diğer sayılar "doğrulanamadı" olarak döner;
metin engellenmez, arayüz kullanıcıya uyarı gösterir.
"""

import re
from collections.abc import Iterable
from typing import Any

NUMBER = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?")


def unverified_numbers(text: str, facts: dict[str, Any], extra: Iterable[float] = ()) -> list[str]:
    allowed = _allowed_values(facts) | {round(float(v), 2) for v in extra}
    found: list[str] = []
    for token in NUMBER.findall(text):
        value = round(float(token.replace(",", ".")), 2)
        if value not in allowed and token not in found:
            found.append(token)
    return found


def _allowed_values(facts: dict[str, Any]) -> set[float]:
    values: set[float] = set()
    _collect(facts, values)
    _differences(facts.get("takim_a", {}), facts.get("takim_b", {}), values)
    return values


def _differences(a: dict[str, Any], b: dict[str, Any], values: set[float]) -> None:
    """Yalnızca aynı metriğin iki takım arasındaki farkı (ör. puan farkı, iç saha puan farkı)."""
    for key, value in a.items():
        other = b.get(key)
        if isinstance(value, dict) and isinstance(other, dict):
            _differences(value, other, values)
        elif isinstance(value, int | float) and isinstance(other, int | float):
            values.add(round(abs(value - other), 2))


def _collect(node: Any, values: set[float]) -> None:
    if isinstance(node, bool):
        return
    if isinstance(node, int | float):
        values.add(round(float(node), 2))
        values.add(round(float(node), 1))
    elif isinstance(node, str):
        for token in NUMBER.findall(node):
            values.add(round(float(token.replace(",", ".")), 2))
    elif isinstance(node, dict):
        for value in node.values():
            _collect(value, values)
    elif isinstance(node, list):
        for value in node:
            _collect(value, values)
