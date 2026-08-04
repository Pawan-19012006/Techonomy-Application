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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    """Schema for returning system events."""

    id: int
    team_id: Optional[int] = None
    event_type: str
    details: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AnalyticsSummaryResponse(BaseModel):
    """Schema summarizing system-wide metrics for administrators."""

    total_teams: int
    total_documents: int
    total_prompts: int
    active_users_today: int
