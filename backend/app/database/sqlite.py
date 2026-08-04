from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings
from app.utils.logging import logger

# SQLite engine configuration (handles multi-threading for FastAPI request threads)
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.SQL_ECHO
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a SQLAlchemy database session.

    Yields:
        Session: Database session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initializes database tables according to SQLAlchemy Declarative models."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")


def reset_db() -> None:
    """Drops and recreates all database tables (For test setups and schema resets)."""
    logger.info("Resetting database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema reset complete.")
