from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Integer, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Constraint isimleri sabit olsun ki Alembic migration'ları deterministik üretilsin.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ExternalIdMixin:
    """Dış API'deki (API-Football) kimlik. Upsert işlemleri bu alan üzerinden yapılır."""

    external_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)


def str_enum(enum_cls: type[StrEnum]) -> Enum:
    """Enum'u DB'de değeriyle (ör. "finished") VARCHAR olarak saklar.

    Native PG enum yerine VARCHAR: yeni değer eklemek migration gerektirmez.
    """
    return Enum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [member.value for member in e],
        length=20,
        validate_strings=True,
    )
