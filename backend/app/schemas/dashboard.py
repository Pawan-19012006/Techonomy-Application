from typing import Optional
from pydantic import BaseModel


class DashboardResponse(BaseModel):
    """Unified response payload for GET /dashboard endpoint."""

    team_name: str
    current_event: Optional[str] = None
    business_objective: Optional[str] = None
    rules: Optional[str] = None
    question_limit: int
    questions_remaining: int
    timer_remaining_seconds: int
    documents_available: int
    event_status: str
