import json
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_json(name: str) -> dict[str, Any]:
    """tests/fixtures altındaki örnek API yanıtını okur."""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def _test_database_url() -> str:
    if url := os.getenv("TEST_DATABASE_URL"):
        return url
    return (
        make_url(get_settings().database_url)
        .set(database="football_test")
        .render_as_string(hide_password=False)
    )


def _ensure_database(url: str) -> None:
    db_url = make_url(url)
    admin_engine = create_engine(db_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": db_url.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{db_url.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    url = _test_database_url()
    _ensure_database(url)
    engine = create_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """Her test kendi transaction'ında çalışır ve sonunda geri alınır."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()
