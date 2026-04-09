"""
Database engine, session factory, and initialization for the Job Aggregator.

Usage
-----
    from src.db.database import init_db, get_session

    init_db()                       # create tables (idempotent)

    with get_session() as session:
        session.add(some_job)
        session.commit()
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import config
from src.core.logger import get_logger
from src.db.models import Base

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _build_engine() -> Engine:
    """Create and return the SQLAlchemy engine for the configured SQLite DB."""
    db_dir = os.path.dirname(config.DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    engine = create_engine(
        f"sqlite:///{config.DB_PATH}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Enable WAL mode for SQLite — better concurrent read performance.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    return engine


# Module-level engine — created once at import time.
_engine: Engine = _build_engine()

# Session factory bound to the engine.
_SessionFactory = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """
    Create all tables defined in the ORM models if they do not yet exist.

    This is idempotent — safe to call on every startup.
    """
    Base.metadata.create_all(bind=_engine)
    logger.info("Database initialized: %s", config.DB_PATH)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy Session, committing on success or rolling back on error.

    Usage:
        with get_session() as session:
            session.add(job)
    """
    session: Session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
