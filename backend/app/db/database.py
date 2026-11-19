"""SQLAlchemy engine/session factory with SQLite-safe transaction settings."""
from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..config import ROOT, settings


class Base(DeclarativeBase):
    pass


def _resolve_url(url: str) -> str:
    # Marketplace Postgres providers hand out a plain postgresql:// URL.
    # SQLAlchemy 2.x needs an explicit driver.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel = url[len("sqlite:///"):]
        path = (ROOT / rel).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"
    return url


_DB_URL = _resolve_url(settings.database_url)
_IS_SQLITE = _DB_URL.startswith("sqlite")

engine = create_engine(
    _DB_URL,
    connect_args=({"check_same_thread": False, "timeout": 30} if _IS_SQLITE else {}),
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn: object, _: object) -> None:
    if engine.dialect.name != "sqlite":
        return
    cur = dbapi_conn.cursor()  # type: ignore[attr-defined]
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=30000")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  — registers tables
    Base.metadata.create_all(bind=engine)


def db_path() -> Path:
    url = _resolve_url(settings.database_url)
    return Path(url[len("sqlite:///"):])
