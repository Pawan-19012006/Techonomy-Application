"""Database configuration supporting Supabase PostgreSQL and SQLite fallback with connection pooling."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings
from app.utils.logging import logger

# Configure SQLAlchemy engine based on DATABASE_URL driver
db_url = settings.DATABASE_URL.strip()

if db_url.startswith("postgresql"):
    logger.info("Initializing SQLAlchemy engine for PostgreSQL (Supabase Pooler)...")
    engine = create_engine(
        db_url,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=settings.SQL_ECHO,
    )
else:
    logger.info("Initializing SQLAlchemy engine for SQLite...")
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=settings.SQL_ECHO,
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


def seed_initial_data(db: Session) -> None:
    """Seeds default team if the database is empty."""
    from app.database.models import TeamModel

    demo_team = db.query(TeamModel).filter(TeamModel.team_name == "TEAM-01").first()
    if not demo_team:
        logger.info("Seeding default event team (TEAM-01)...")
        demo_team = TeamModel(
            team_name="TEAM-01",
            member_names=["Pawan", "Rahul", "Kabilan"],
        )
        db.add(demo_team)
        db.commit()


def init_db() -> None:
    """Initializes database tables according to SQLAlchemy Declarative models and seeds default data."""
    import app.database.models  # Ensure models are registered on Base.metadata
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")

    db = SessionLocal()
    try:
        seed_initial_data(db)
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_db() -> None:
    """Drops and recreates all database tables (For test setups and schema resets)."""
    import app.database.models  # Ensure models are registered on Base.metadata
    logger.info("Resetting database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema reset complete.")
