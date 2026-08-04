from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PromptLogResponse(BaseModel):
    """Schema for returning audit prompt log entries."""

    id: int
    team_id: int
    prompt: str
    response: Optional[str] = None
    status_code: int
    response_time_ms: float = 0.0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventResponseSchema(BaseModel):
    """Schema for returning audit logs."""

    id: int
    team_id: Optional[int] = None
    event_type: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummaryResponse(BaseModel):
    """Schema summarizing system-wide metrics for administrators."""

    total_teams: int
    active_teams: int
    questions_used: int
    questions_remaining: int
    total_prompts: int
    average_response_time_ms: float
    most_active_team: Optional[str] = "N/A"
    most_used_document: Optional[str] = "N/A"
