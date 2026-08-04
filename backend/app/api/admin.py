from datetime import datetime
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.admin import AnalyticsSummaryResponse, PromptLogResponse
from app.schemas.document import DocumentMetadataResponse
from app.schemas.event import EventStatusResponse
from app.schemas.team import TeamResponse
from app.services.analytics import AnalyticsService
from app.services.document_service import DocumentService
from app.services.event_service import EventService
from app.services.team_service import TeamService
from app.services.timer_service import TimerService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get("/teams", response_model=List[TeamResponse], summary="View All Registered Teams (Admin)")
async def list_all_teams(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> List[TeamResponse]:
    """Retrieves all registered Teams with question usage metrics (Administrator permission required)."""
    return TeamService.list_all_teams(db)


@router.get("/prompts", response_model=List[PromptLogResponse], summary="View and Filter Prompt Logs (Admin)")
async def view_prompt_logs(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    team_id: Optional[int] = Query(None, description="Filter logs by Team ID"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from UTC date"),
    date_to: Optional[datetime] = Query(None, description="Filter logs up to UTC date"),
    limit: int = Query(100, description="Maximum log entries to return")
) -> List[PromptLogResponse]:
    """Retrieves system prompt query logs with optional filtering (Administrator permission required)."""
    return AnalyticsService.get_prompt_logs(db, team_id=team_id, date_from=date_from, date_to=date_to, limit=limit)


@router.get("/documents", response_model=List[DocumentMetadataResponse], summary="View All Uploaded Documents (Admin)")
async def list_all_documents(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> List[DocumentMetadataResponse]:
    """Retrieves metadata for all uploaded documents across all teams (Administrator permission required)."""
    return DocumentService.list_all_documents(db)


@router.get("/analytics", response_model=AnalyticsSummaryResponse, summary="View Competition Platform Analytics (Admin)")
async def view_analytics(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> AnalyticsSummaryResponse:
    """Retrieves aggregate platform analytics including teams, questions, prompts, and response times."""
    return AnalyticsService.get_analytics_summary(db)


@router.get("/event/status", response_model=EventStatusResponse, summary="View Active Event Status (Admin)")
async def view_admin_event_status(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> EventStatusResponse:
    """Retrieves status and backend timer information for the active event (Administrator permission required)."""
    event = EventService.get_active_event(db)
    state = EventService.compute_event_state(event)
    timer_info = TimerService.calculate_event_timer(event)

    return EventStatusResponse(
        event_id=event.id if event else None,
        event_name=event.name if event else None,
        status=state,
        start_time=event.start_time if event else None,
        end_time=event.end_time if event else None,
        question_limit=event.question_limit if event else 0,
        timer_remaining_seconds=timer_info["remaining_seconds"],
        started=timer_info["started"],
        finished=timer_info["finished"]
    )
