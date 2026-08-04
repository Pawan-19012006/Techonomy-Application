from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.sqlite import Base


def utc_now() -> datetime:
    """Returns current UTC timestamp."""
    return datetime.now(timezone.utc)


class TeamModel(Base):
    """SQLAlchemy model representing an enterprise Team / User account."""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    question_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    questions_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    documents: Mapped[List["DocumentModel"]] = relationship("DocumentModel", back_populates="team", cascade="all, delete-orphan")
    prompt_logs: Mapped[List["PromptLogModel"]] = relationship("PromptLogModel", back_populates="team", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLogModel"]] = relationship("AuditLogModel", back_populates="team", cascade="all, delete-orphan")


class EventModel(Base):
    """SQLAlchemy model representing a Competition Event."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    question_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DocumentModel(Base):
    """SQLAlchemy model representing uploaded Document metadata."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    pages: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="ready", nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    team: Mapped["TeamModel"] = relationship("TeamModel", back_populates="documents")


class PromptLogModel(Base):
    """SQLAlchemy model logging prompt queries and API interactions."""

    __tablename__ = "prompt_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status_code: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    team: Mapped["TeamModel"] = relationship("TeamModel", back_populates="prompt_logs")


class AuditLogModel(Base):
    """SQLAlchemy model for tracking system events and audit logs."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationship
    team: Mapped[Optional["TeamModel"]] = relationship("TeamModel", back_populates="audit_logs")
