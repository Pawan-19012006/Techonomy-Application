"""Data migration script migrating application records from SQLite (techonomy.db) to Supabase PostgreSQL."""

from datetime import datetime
import json
from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session
from app.config import settings
from app.database.models import (
    AuditLogModel,
    DocumentModel,
    EventModel,
    PromptLogModel,
    TeamModel,
)
from app.database.db import Base, SessionLocal, engine
from app.utils.logging import logger


def parse_datetime(dt_val):
    """Safely converts string or datetime to Python datetime object."""
    if not dt_val:
        return None
    if isinstance(dt_val, datetime):
        return dt_val
    try:
        # ISO format or standard string format
        return datetime.fromisoformat(str(dt_val).replace("Z", "+00:00"))
    except Exception:
        return datetime.now()


def migrate_data():
    print("\n" + "=" * 90)
    print(" 🚚 MIGRATING DATA FROM SQLITE (techonomy.db) TO SUPABASE POSTGRESQL")
    print("=" * 90 + "\n")

    sqlite_db_path = PROJECT_ROOT / "techonomy.db"
    if not sqlite_db_path.exists():
        print(f"SQLite database file '{sqlite_db_path}' not found. Skipping data migration.")
        return

    # 1. Initialize PostgreSQL tables
    print("1. Ensuring all PostgreSQL tables exist...")
    Base.metadata.create_all(bind=engine)
    print("   PostgreSQL schema initialized successfully.\n")

    # 2. Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    pg_session: Session = SessionLocal()

    try:
        # Table 1: Teams
        print("2. Migrating 'teams' table...")
        sqlite_cur.execute("SELECT * FROM teams;")
        teams_rows = [dict(r) for r in sqlite_cur.fetchall()]
        sqlite_teams_count = len(teams_rows)

        for row in teams_rows:
            team_name = str(row["team_name"]).strip()
            existing = pg_session.query(TeamModel).filter(TeamModel.team_name == team_name).first()
            if not existing:
                raw_members = row["member_names"]
                if isinstance(raw_members, str):
                    members = json.loads(raw_members)
                else:
                    members = list(raw_members)

                new_team = TeamModel(
                    team_name=team_name,
                    member_names=members,
                    started_at=parse_datetime(row["started_at"]),
                )
                pg_session.add(new_team)

        pg_session.commit()
        pg_teams_count = pg_session.query(TeamModel).count()
        print(f"   teams count: SQLite = {sqlite_teams_count} | PostgreSQL = {pg_teams_count}")

        # Table 2: Prompt Logs
        print("3. Migrating 'prompt_logs' table...")
        sqlite_cur.execute("SELECT * FROM prompt_logs;")
        prompts_rows = [dict(r) for r in sqlite_cur.fetchall()]
        sqlite_prompts_count = len(prompts_rows)

        for row in prompts_rows:
            p_id = int(row["id"])
            existing = pg_session.query(PromptLogModel).filter(PromptLogModel.id == p_id).first()
            if not existing:
                new_prompt = PromptLogModel(
                    id=p_id,
                    team_name=str(row["team_name"]).strip(),
                    prompt=str(row["prompt"]),
                    response=str(row["response"]),
                    created_at=parse_datetime(row["created_at"]),
                )
                pg_session.add(new_prompt)

        pg_session.commit()
        pg_prompts_count = pg_session.query(PromptLogModel).count()
        print(f"   prompt_logs count: SQLite = {sqlite_prompts_count} | PostgreSQL = {pg_prompts_count}")

        # Table 3: Events
        print("4. Migrating 'events' table...")
        sqlite_cur.execute("SELECT * FROM events;")
        events_rows = [dict(r) for r in sqlite_cur.fetchall()]
        sqlite_events_count = len(events_rows)

        for row in events_rows:
            e_id = int(row["id"])
            existing = pg_session.query(EventModel).filter(EventModel.id == e_id).first()
            if not existing:
                new_event = EventModel(
                    id=e_id,
                    name=str(row["name"]),
                    description=row.get("description"),
                    business_objective=row.get("business_objective"),
                    rules=row.get("rules"),
                    start_time=parse_datetime(row["start_time"]),
                    end_time=parse_datetime(row["end_time"]),
                    question_limit=int(row.get("question_limit", 10)),
                    is_active=bool(row.get("is_active", True)),
                    created_at=parse_datetime(row["created_at"]),
                )
                pg_session.add(new_event)

        pg_session.commit()
        pg_events_count = pg_session.query(EventModel).count()
        print(f"   events count: SQLite = {sqlite_events_count} | PostgreSQL = {pg_events_count}")

        # Table 4: Documents
        print("5. Migrating 'documents' table...")
        sqlite_cur.execute("SELECT * FROM documents;")
        doc_rows = [dict(r) for r in sqlite_cur.fetchall()]
        sqlite_docs_count = len(doc_rows)

        for row in doc_rows:
            d_id = int(row["id"])
            existing = pg_session.query(DocumentModel).filter(DocumentModel.id == d_id).first()
            if not existing:
                new_doc = DocumentModel(
                    id=d_id,
                    filename=str(row["filename"]),
                    file_path=str(row["file_path"]),
                    file_size=int(row["file_size"]),
                    content_type=str(row["content_type"]),
                    pages=int(row["pages"]),
                    status=str(row["status"]),
                    team_id=int(row["team_id"]),
                    uploaded_at=parse_datetime(row["uploaded_at"]),
                )
                pg_session.add(new_doc)

        pg_session.commit()
        pg_docs_count = pg_session.query(DocumentModel).count()
        print(f"   documents count: SQLite = {sqlite_docs_count} | PostgreSQL = {pg_docs_count}")

        # Table 5: Audit Logs
        print("6. Migrating 'audit_logs' table...")
        sqlite_cur.execute("SELECT * FROM audit_logs;")
        audit_rows = [dict(r) for r in sqlite_cur.fetchall()]
        sqlite_audit_count = len(audit_rows)

        for row in audit_rows:
            a_id = int(row["id"])
            existing = pg_session.query(AuditLogModel).filter(AuditLogModel.id == a_id).first()
            if not existing:
                new_audit = AuditLogModel(
                    id=a_id,
                    team_id=row.get("team_id"),
                    event_type=str(row["event_type"]),
                    details=row.get("details"),
                    timestamp=parse_datetime(row["timestamp"]),
                )
                pg_session.add(new_audit)

        pg_session.commit()
        pg_audit_count = pg_session.query(AuditLogModel).count()
        print(f"   audit_logs count: SQLite = {sqlite_audit_count} | PostgreSQL = {pg_audit_count}")

        print("\n" + "=" * 90)
        print(" 🎉 MIGRATION SUMMARY & VERIFICATION")
        print("=" * 90)
        print(f"  • teams:       SQLite={sqlite_teams_count} | PostgreSQL={pg_teams_count} (Match: {sqlite_teams_count == pg_teams_count})")
        print(f"  • prompt_logs: SQLite={sqlite_prompts_count} | PostgreSQL={pg_prompts_count} (Match: {sqlite_prompts_count == pg_prompts_count})")
        print(f"  • events:      SQLite={sqlite_events_count} | PostgreSQL={pg_events_count} (Match: {sqlite_events_count == pg_events_count})")
        print(f"  • documents:   SQLite={sqlite_docs_count} | PostgreSQL={pg_docs_count} (Match: {sqlite_docs_count == pg_docs_count})")
        print(f"  • audit_logs:  SQLite={sqlite_audit_count} | PostgreSQL={pg_audit_count} (Match: {sqlite_audit_count == pg_audit_count})")
        print("=" * 90 + "\n")

    except Exception as e:
        pg_session.rollback()
        print(f"❌ Migration failed with error: {e}")
        raise e
    finally:
        sqlite_conn.close()
        pg_session.close()


if __name__ == "__main__":
    migrate_data()
