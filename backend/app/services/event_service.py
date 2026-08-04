from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import EventModel
from app.schemas.event import EventCreate, EventUpdate
from app.services.timer_service import TimerService
from app.utils.logging import logger


class EventService:
    """Service handling Competition Event lifecycle and status calculation."""

    @staticmethod
    def compute_event_state(event: Optional[EventModel]) -> str:
        """Calculates dynamic state of an event from current UTC server time.

        Args:
            event: Event database object or None.

        Returns:
            str: State classification ('UPCOMING', 'ACTIVE', 'PAUSED', 'COMPLETED', or 'NO_EVENT').
        """
        if not event:
            return "NO_EVENT"

        if not event.is_active:
            return "PAUSED"

        now = datetime.now(timezone.utc)
        start = event.start_time
        end = event.end_time

        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        if now < start:
            return "UPCOMING"
        elif start <= now <= end:
            return "ACTIVE"
        else:
            return "COMPLETED"

    @staticmethod
    def get_active_event(db: Session) -> Optional[EventModel]:
        """Retrieves the currently active or most recently created competition event.

        Args:
            db: Database session.

        Returns:
            Optional[EventModel]: Event record or None.
        """
        active_event = db.query(EventModel).filter(EventModel.is_active == True).order_by(EventModel.start_time.desc()).first()
        if not active_event:
            active_event = db.query(EventModel).order_by(EventModel.created_at.desc()).first()
        return active_event

    @staticmethod
    def get_event_by_id(db: Session, event_id: int) -> Optional[EventModel]:
        """Retrieves an event by primary key ID.

        Args:
            db: Database session.
            event_id: Primary key event ID.

        Returns:
            Optional[EventModel]: Event record or None.
        """
        return db.query(EventModel).filter(EventModel.id == event_id).first()

    @staticmethod
    def list_events(db: Session) -> List[EventModel]:
        """Lists all competition events.

        Args:
            db: Database session.

        Returns:
            List[EventModel]: List of all event records.
        """
        return db.query(EventModel).order_by(EventModel.created_at.desc()).all()

    @staticmethod
    def create_event(db: Session, event_data: EventCreate) -> EventModel:
        """Creates a new Competition Event.

        Args:
            db: Database session.
            event_data: Event creation payload.

        Returns:
            EventModel: Created event record.
        """
        new_event = EventModel(
            name=event_data.name,
            description=event_data.description,
            business_objective=event_data.business_objective,
            rules=event_data.rules,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            question_limit=event_data.question_limit,
            is_active=event_data.is_active
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        logger.info(f"Created new Competition Event '{new_event.name}' (ID: {new_event.id}).")
        return new_event

    @staticmethod
    def update_event(db: Session, event_id: int, event_data: EventUpdate) -> Optional[EventModel]:
        """Updates an existing Competition Event.

        Args:
            db: Database session.
            event_id: Event ID to update.
            event_data: Fields to update.

        Returns:
            Optional[EventModel]: Updated event record or None.
        """
        event = EventService.get_event_by_id(db, event_id)
        if not event:
            return None

        update_dict = event_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(event, key, value)

        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"Updated Competition Event ID {event.id}.")
        return event

    @staticmethod
    def set_event_active_status(db: Session, event_id: int, is_active: bool) -> Optional[EventModel]:
        """Activates or deactivates an event.

        Args:
            db: Database session.
            event_id: Target event ID.
            is_active: Target active status.

        Returns:
            Optional[EventModel]: Updated event record or None.
        """
        event = EventService.get_event_by_id(db, event_id)
        if not event:
            return None

        event.is_active = is_active
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"Set active status of Event ID {event.id} to {is_active}.")
        return event
