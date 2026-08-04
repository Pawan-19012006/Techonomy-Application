from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class TeamCreate(BaseModel):
    """Schema for registering a new Team account."""

    name: str
    email: EmailStr
    password: str
    question_limit: int = 10
    is_admin: bool = False


class TeamResponse(BaseModel):
    """Public response schema for Team details."""

    id: int
    name: str
    email: EmailStr
    question_limit: int
    questions_used: int
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamUsageResponse(BaseModel):
    """Schema for querying Team question usage metrics."""

    team_id: int
    question_limit: int
    questions_used: int
    remaining_questions: int

    model_config = ConfigDict(from_attributes=True)
