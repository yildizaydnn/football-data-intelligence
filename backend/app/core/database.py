from collections.abc import Iterator
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)


@event.listens_for(Engine, "connect")
def _use_utc(dbapi_connection: Any, _record: Any) -> None:
    """Her bağlantıda oturum saat dilimini UTC yapar.

    Zamanlar veritabanı sunucusunun veya istemcinin (PGTZ) ayarından bağımsız olarak hep +00:00
    ile okunur; API çıktısı ve testler her ortamda aynı kalır.
    """
    with dbapi_connection.cursor() as cursor:
        cursor.execute("SET TIME ZONE 'UTC'")
    dbapi_connection.commit()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
