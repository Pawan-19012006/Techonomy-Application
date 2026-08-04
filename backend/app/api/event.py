from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin, get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.event import EventCreate, EventResponse, EventStatusResponse, EventUpdate
from app.services.event_service import EventService
from app.services.timer_service import TimerService

router = APIRouter(prefix="/event", tags=["Event Management"])


@router.get("", response_model=EventResponse, summary="Get Active Event Details")
async def get_active_event(
    db: Annotated[Session, Depends(get_db)],
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> EventResponse:
    """Retrieves details for the currently active Competition Event."""
    event = EventService.get_active_event(db)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active competition event found"
        )
    event_state = EventService.compute_event_state(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        business_objective=event.business_objective,
        rules=event.rules,
        start_time=event.start_time,
        end_time=event.end_time,
        question_limit=event.question_limit,
        is_active=event.is_active,
        status=event_state,
        created_at=event.created_at
    )


@router.get("/status", response_model=EventStatusResponse, summary="Get Active Event Status and Timer")
async def get_event_status(
    db: Annotated[Session, Depends(get_db)],
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> EventStatusResponse:
    """Returns dynamic event status and backend-calculated timer remaining."""
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


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED, summary="Create Competition Event (Admin)")
async def create_event(
    event_data: EventCreate,
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> EventResponse:
    """Creates a new Competition Event (Administrator permission required)."""
    event = EventService.create_event(db, event_data)
    state = EventService.compute_event_state(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        business_objective=event.business_objective,
        rules=event.rules,
        start_time=event.start_time,
        end_time=event.end_time,
        question_limit=event.question_limit,
        is_active=event.is_active,
        status=state,
        created_at=event.created_at
    )


@router.put("/{event_id}", response_model=EventResponse, summary="Update Competition Event (Admin)")
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> EventResponse:
    """Updates an existing Competition Event (Administrator permission required)."""
    event = EventService.update_event(db, event_id, event_data)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event ID {event_id} not found"
        )
    state = EventService.compute_event_state(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        business_objective=event.business_objective,
        rules=event.rules,
        start_time=event.start_time,
        end_time=event.end_time,
        question_limit=event.question_limit,
        is_active=event.is_active,
        status=state,
        created_at=event.created_at
    )


@router.patch("/{event_id}/activate", response_model=EventResponse, summary="Activate Competition Event (Admin)")
async def activate_event(
    event_id: int,
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> EventResponse:
    """Activates a Competition Event (Administrator permission required)."""
    event = EventService.set_event_active_status(db, event_id, is_active=True)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event ID {event_id} not found"
        )
    state = EventService.compute_event_state(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        business_objective=event.business_objective,
        rules=event.rules,
        start_time=event.start_time,
        end_time=event.end_time,
        question_limit=event.question_limit,
        is_active=event.is_active,
        status=state,
        created_at=event.created_at
    )


@router.patch("/{event_id}/deactivate", response_model=EventResponse, summary="Deactivate Competition Event (Admin)")
async def deactivate_event(
    event_id: int,
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> EventResponse:
    """Deactivates a Competition Event (Administrator permission required)."""
    event = EventService.set_event_active_status(db, event_id, is_active=False)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event ID {event_id} not found"
        )
    state = EventService.compute_event_state(event)
    return EventResponse(
        id=event.id,
        name=event.name,
        description=event.description,
        business_objective=event.business_objective,
        rules=event.rules,
        start_time=event.start_time,
        end_time=event.end_time,
        question_limit=event.question_limit,
        is_active=event.is_active,
        status=state,
        created_at=event.created_at
    )
