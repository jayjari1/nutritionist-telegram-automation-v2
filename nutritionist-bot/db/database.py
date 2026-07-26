"""
db/database.py — SQLAlchemy engine, session factory, and schema creation.

Call `init_db()` once at startup. Then use `get_session()` as a context
manager anywhere you need database access.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from db.models import Base
import config

# ---------------------------------------------------------------------------
# Engine — SQLite for demo. Switch URL to postgresql+psycopg2://... for prod.
# NOTE: For production with 200+ concurrent clients, migrate to PostgreSQL.
# ---------------------------------------------------------------------------
_db_dir = os.path.dirname(config.DB_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)

engine = create_engine(
    f"sqlite:///{config.DB_PATH}",
    connect_args={"check_same_thread": False},  # required for SQLite + threading
    echo=False,  # set True to log all SQL for debugging
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call multiple times."""
    Base.metadata.create_all(bind=engine)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE clients ADD COLUMN custom_instructions TEXT;"))
            conn.commit()
    except Exception:
        pass  # column already exists
    print(f"[DB] SQLite database ready at: {config.DB_PATH}")


@contextmanager
def get_session() -> Session:
    """
    Context manager for database sessions.

    Usage:
        with get_session() as session:
            client = session.query(Client).first()
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
