from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict

from app.schemas.admin import PromptLogResponse


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


class TeamQuestionMetricsResponse(BaseModel):
    """Detailed question usage response model for GET /team/questions."""

    question_limit: int
    questions_used: int
    questions_remaining: int


class TeamHistoryResponse(BaseModel):
    """Response payload for Team prompt execution history."""

    logs: List[PromptLogResponse]
    total_count: int
