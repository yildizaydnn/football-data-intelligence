from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, ClassVar

from sqlalchemy import ColumnElement, func, literal_column, select, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.base import Base


@dataclass(frozen=True)
class UpsertResult:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0

    def __add__(self, other: UpsertResult) -> UpsertResult:
        return UpsertResult(
            self.inserted + other.inserted,
            self.updated + other.updated,
            self.unchanged + other.unchanged,
        )


class BaseRepository[ModelT: Base]:
    """Ortak CRUD + upsert. Alt sınıflar sadece `model` ve gerekiyorsa özel sorgular tanımlar."""

    model: type[ModelT]
    upsert_keys: ClassVar[tuple[str, ...]] = ("external_id",)

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id: int) -> ModelT | None:
        return self.session.get(self.model, id)

    def list(
        self,
        *filters: ColumnElement[bool],
        order_by: Sequence[Any] = (),
        limit: int | None = None,
        offset: int = 0,
    ) -> list[ModelT]:
        stmt = select(self.model).where(*filters).order_by(*order_by).offset(offset).limit(limit)
        return list(self.session.scalars(stmt))

    def count(self, *filters: ColumnElement[bool]) -> int:
        stmt = select(func.count()).select_from(self.model).where(*filters)
        return self.session.scalar(stmt) or 0

    def get_by_external_id(self, external_id: int) -> ModelT | None:
        stmt = select(self.model).where(self.model.external_id == external_id)
        return self.session.scalar(stmt)

    def id_map(self, external_ids: Sequence[int]) -> dict[int, int]:
        """external_id → iç id eşlemesi (FK çözümlemek için)."""
        if not external_ids:
            return {}
        stmt = select(self.model.external_id, self.model.id).where(
            self.model.external_id.in_(set(external_ids))
        )
        return dict(self.session.execute(stmt).all())

    def upsert(self, items: Sequence[dict[str, Any]]) -> UpsertResult:
        """INSERT ... ON CONFLICT (upsert_keys) DO UPDATE.

        Değeri değişmeyen satırlara dokunulmaz (updated_at da değişmez), bu yüzden
        aynı veri tekrar geldiğinde sonuç `unchanged` olarak sayılır.
        """
        rows = self._dedupe(items)
        if not rows:
            return UpsertResult()

        table = self.model.__table__
        stmt = insert(table).values(rows)
        update_cols = [c for c in rows[0] if c not in self.upsert_keys]

        if update_cols:
            set_: dict[str, Any] = {c: stmt.excluded[c] for c in update_cols}
            if "updated_at" in table.c:
                set_["updated_at"] = func.now()
            stmt = stmt.on_conflict_do_update(
                index_elements=list(self.upsert_keys),
                set_=set_,
                where=tuple_(*(table.c[c] for c in update_cols)).is_distinct_from(
                    tuple_(*(stmt.excluded[c] for c in update_cols))
                ),
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=list(self.upsert_keys))

        # PostgreSQL'de yeni eklenen satırın xmax değeri 0'dır; güncellenen satırınki değildir.
        flags = self.session.scalars(stmt.returning(literal_column("xmax = 0"))).all()
        inserted = sum(1 for is_insert in flags if is_insert)
        updated = len(flags) - inserted
        return UpsertResult(inserted, updated, len(rows) - inserted - updated)

    def _dedupe(self, items: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        # Aynı komutta aynı anahtar iki kez olursa PG hata verir; son gelen kazanır.
        unique: dict[tuple[Any, ...], dict[str, Any]] = {}
        for item in items:
            unique[tuple(item[k] for k in self.upsert_keys)] = item
        return list(unique.values())
