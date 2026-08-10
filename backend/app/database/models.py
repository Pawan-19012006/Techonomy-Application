from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
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
