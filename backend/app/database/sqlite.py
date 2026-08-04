from datetime import datetime, timedelta, timezone
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


def seed_initial_data(db: Session) -> None:
    """Seeds initial demo teams and active event if the database is empty."""
    from app.database.models import TeamModel, EventModel
    from app.auth.password import hash_password

    # Seed demo team if not exists
    demo_team = db.query(TeamModel).filter(TeamModel.email == "devs@acme.com").first()
    if not demo_team:
        logger.info("Seeding default demo team (devs@acme.com)...")
        demo_team = TeamModel(
            name="Team 14",
            email="devs@acme.com",
            hashed_password=hash_password("SecretPassword123!"),
            question_limit=10,
            questions_used=0,
            is_admin=False
        )
        db.add(demo_team)

    # Seed admin team if not exists
    admin_team = db.query(TeamModel).filter(TeamModel.email == "admin@techonomy.com").first()
    if not admin_team:
        logger.info("Seeding default admin team (admin@techonomy.com)...")
        admin_team = TeamModel(
            name="System Administrator",
            email="admin@techonomy.com",
            hashed_password=hash_password("AdminPassword123!"),
            question_limit=100,
            questions_used=0,
            is_admin=True
        )
        db.add(admin_team)

    # Seed active competition event only if no events exist at all
    any_event = db.query(EventModel).first()
    if not any_event:
        logger.info("Seeding default active competition event...")
        now = datetime.now(timezone.utc)
        active_event = EventModel(
            name="ABC Retail Pvt Ltd.",
            description="Analyze company documents, financial statements, and market research reports to deliver actionable revenue growth strategies.",
            business_objective="Increase Revenue by 20%",
            rules="10 questions maximum per team. 2 hour 45 minute time limit.",
            start_time=now - timedelta(minutes=15),
            end_time=now + timedelta(hours=2, minutes=45),
            question_limit=10,
            is_active=True
        )
        db.add(active_event)

    db.commit()


def init_db() -> None:
    """Initializes database tables according to SQLAlchemy Declarative models and seeds default data."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    db = SessionLocal()
    try:
        seed_initial_data(db)
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()


def reset_db() -> None:
    """Drops and recreates all database tables (For test setups and schema resets)."""
    logger.info("Resetting database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema reset complete.")
