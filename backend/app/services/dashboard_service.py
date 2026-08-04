from sqlalchemy.orm import Session

from app.database.models import TeamModel
from app.schemas.dashboard import DashboardResponse
from app.services.document_service import DocumentService
from app.services.event_service import EventService
from app.services.timer_service import TimerService


class DashboardService:
    """Service producing unified Dashboard metrics for frontend consumption."""

    @staticmethod
    def get_team_dashboard(db: Session, team: TeamModel) -> DashboardResponse:
        """Aggregates all competition metrics into a single response object.

        Args:
            db: Database session.
            team: Authenticated team database model.

        Returns:
            DashboardResponse: Aggregated payload.
        """
        active_event = EventService.get_active_event(db)
        event_status = EventService.compute_event_state(active_event)
        timer_info = TimerService.calculate_event_timer(active_event)
        doc_count = DocumentService.count_team_documents(db, team.id)

        questions_remaining = max(0, team.question_limit - team.questions_used)

        return DashboardResponse(
            team_name=team.name,
            current_event=active_event.name if active_event else None,
            business_objective=active_event.business_objective if active_event else None,
            rules=active_event.rules if active_event else None,
            question_limit=team.question_limit,
            questions_remaining=questions_remaining,
            timer_remaining_seconds=timer_info["remaining_seconds"],
            documents_available=doc_count,
            event_status=event_status
        )
