from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.sqlite import Base


def utc_now() -> datetime:
    """Returns current UTC timestamp in ISO/timezone-aware format."""
    return datetime.now(timezone.utc)


class TeamModel(Base):
    """SQLAlchemy model representing an event Team.

    Attributes:
        team_name (str): Team name acts as the Primary Key.
        member_names (List[str]): Array of member names stored as JSON.
        started_at (datetime): Timestamp when team joined the arena.
    """

    __tablename__ = "teams"

    team_name: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    member_names: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship to prompt logs submitted by team
    prompt_logs: Mapped[List["PromptLogModel"]] = relationship(
        "PromptLogModel", back_populates="team", cascade="all, delete-orphan"
    )


class PromptLogModel(Base):
    """SQLAlchemy model logging prompt queries submitted by teams.

    Attributes:
        id (int): Primary Key autoincrement ID.
        team_name (str): Foreign key referencing teams.team_name.
        prompt (str): User question text.
        response (str): RAG generated response text.
        created_at (datetime): Submission timestamp.
    """

    __tablename__ = "prompt_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    team_name: Mapped[str] = mapped_column(
        String(100), ForeignKey("teams.team_name", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship back to TeamModel
    team: Mapped["TeamModel"] = relationship("TeamModel", back_populates="prompt_logs")


class EventModel(Base):
    """SQLAlchemy model representing an Event."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    question_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DocumentModel(Base):
    """SQLAlchemy model representing an uploaded Document."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLogModel(Base):
    """SQLAlchemy model representing an Audit Log entry."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
