"""
Database Connection & Session Management for kartavya (Phase 9 Public Multi-User Architecture).

Handles engine initialization, connection pooling for Neon PostgreSQL / SQLite,
Streamlit secrets resolution ([database] url, DATABASE_URL), and graceful error handling.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.db.models import Base

logger = logging.getLogger(__name__)

# Global Engine & Session Factory singletons
_ENGINE = None
_SESSION_FACTORY = None


class DatabaseConnectionError(Exception):
    """Custom exception raised when the database service is unreachable or errors occur."""
    pass


def get_database_url() -> str:
    """
    Resolves canonical DATABASE_URL from Streamlit secrets or environment.
    Supports [database] url, DATABASE_URL, and [postgres] url keys.
    Defaults to local SQLite if unspecified.
    """
    db_url = None

    try:
        if hasattr(st, "secrets"):
            if "database" in st.secrets and "url" in st.secrets["database"]:
                db_url = st.secrets["database"]["url"]
            elif "DATABASE_URL" in st.secrets:
                db_url = st.secrets["DATABASE_URL"]
            elif "postgres" in st.secrets and "url" in st.secrets["postgres"]:
                db_url = st.secrets["postgres"]["url"]
    except Exception:
        pass

    if not db_url:
        db_url = os.getenv("DATABASE_URL")

    if not db_url:
        # Local SQLite fallback
        from src.config import KARTAVYA_DATA_DIR
        os.makedirs(KARTAVYA_DATA_DIR, exist_ok=True)
        db_path = os.path.join(KARTAVYA_DATA_DIR, "kartavya_db.sqlite")
        db_url = f"sqlite:///{db_path}"

    # Standardize protocol prefix for SQLAlchemy compatibility (postgres:// -> postgresql://)
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return db_url


def get_engine():
    """Returns singleton SQLAlchemy Engine with pooling configured for Neon PostgreSQL."""
    global _ENGINE
    if _ENGINE is None:
        db_url = get_database_url()
        is_sqlite = db_url.startswith("sqlite")

        engine_kwargs = {}
        if is_sqlite:
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        else:
            engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
            engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
            engine_kwargs["pool_pre_ping"] = True
            engine_kwargs["pool_recycle"] = 300  # Recycle connections every 5 mins for serverless Neon DBs

        _ENGINE = create_engine(db_url, **engine_kwargs)
        logger.info(f"Initialized SQLAlchemy Engine (SQLite: {is_sqlite})")

    return _ENGINE


def get_session_factory():
    """Returns singleton SessionLocal factory."""
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        engine = get_engine()
        _SESSION_FACTORY = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SESSION_FACTORY


def init_db() -> None:
    """Creates database tables idempotently if they do not exist."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise DatabaseConnectionError("Kartavya is temporarily unable to connect to its data service. Please try again.") from e


def test_connection() -> bool:
    """Tests if the database engine is connected and operational."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check connection failure: {e}")
        return False


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager supplying a transactional database session."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database transaction error: {e}")
        raise DatabaseConnectionError("Kartavya is temporarily unable to connect to its data service. Please try again.") from e
    finally:
        session.close()
