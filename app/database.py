"""SQLAlchemy engine, session factory and declarative base."""
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry

from app.config import settings

# check_same_thread is required because FastAPI serves requests from a thread pool.
engine = create_engine(
    settings.database_url, connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_connection: DBAPIConnection, _record: ConnectionPoolEntry) -> None:
    """WAL lets readers and a writer coexist; busy_timeout makes concurrent
    writers (e.g. several uvicorn workers) wait instead of failing with
    'database is locked'."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a session that is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
