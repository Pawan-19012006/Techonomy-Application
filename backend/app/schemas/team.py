"""Pydantic schemas for Team API requests and responses."""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class TeamJoinRequest(BaseModel):
    """Payload schema for joining an event arena."""

    team_name: str = Field(..., description="Unique team identifier name", min_length=1, max_length=100)
    member_names: List[str] = Field(..., description="List of team member full names", min_length=1)



class TeamResponse(BaseModel):
    """Response schema representing an active event team."""

    team_name: str = Field(..., description="Team name primary key")
    member_names: List[str] = Field(..., description="List of member names")
    started_at: datetime = Field(..., description="Timestamp when team started arena session")


class PromptLogResponse(BaseModel):
    """Response schema for prompt execution log entry."""

    id: int = Field(..., description="Prompt log ID")
    prompt: str = Field(..., description="Submitted question prompt")
    response: str = Field(..., description="Generated RAG answer text")
    created_at: datetime = Field(..., description="Submission timestamp")
