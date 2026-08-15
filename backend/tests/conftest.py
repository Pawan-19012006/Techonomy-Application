"""Global pytest configuration and database fixtures for clean isolation across full test suite runs."""

import pytest
from app.database.db import SessionLocal, init_db
from app.database.models import LLMLaneModel, TeamQuotaModel, PromptLogModel, TeamModel


@pytest.fixture(autouse=True)
def reset_database_isolation():
    """Resets database state and LLM lane metrics before every test to guarantee test isolation."""
    init_db()
    db = SessionLocal()
    try:
        db.query(LLMLaneModel).update({
            "requests_used": 0,
            "active_requests": 0,
            "state": "AVAILABLE",
            "cooldown_until": None,
            "error_count": 0,
        })
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    yield
