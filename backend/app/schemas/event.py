from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    """Schema for creating a Competition Event."""

    name: str
    description: Optional[str] = None
    business_objective: Optional[str] = None
    rules: Optional[str] = None
    start_time: datetime
    end_time: datetime
    question_limit: int = 10
    is_active: bool = True


class EventUpdate(BaseModel):
    """Schema for updating a Competition Event."""

    name: Optional[str] = None
    description: Optional[str] = None
    business_objective: Optional[str] = None
    rules: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    question_limit: Optional[int] = None
    is_active: Optional[bool] = None


class EventResponse(BaseModel):
    """Public response schema for Competition Event details."""

    id: int
    name: str
    description: Optional[str] = None
    business_objective: Optional[str] = None
    rules: Optional[str] = None
    start_time: datetime
    end_time: datetime
    question_limit: int
    is_active: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventStatusResponse(BaseModel):
    """Response schema summarizing event state and backend timer values."""

    event_id: Optional[int] = None
    event_name: Optional[str] = None
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    question_limit: int = 0
    timer_remaining_seconds: int = 0
    started: bool = False
    finished: bool = False
