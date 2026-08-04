from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import DocumentModel, EventModel, PromptLogModel, TeamModel
from app.schemas.admin import AnalyticsSummaryResponse
from app.utils.logging import logger


class AnalyticsService:
    """Service providing aggregate usage metrics, prompt logs, and event tracking."""

    @staticmethod
    def get_analytics_summary(db: Session) -> AnalyticsSummaryResponse:
        """Computes system-wide analytics for administration.

        Args:
            db: Database session.

        Returns:
            AnalyticsSummaryResponse: Metrics summary.
        """
        total_teams = db.query(func.count(TeamModel.id)).scalar() or 0
        total_documents = db.query(func.count(DocumentModel.id)).scalar() or 0
        total_prompts = db.query(func.count(PromptLogModel.id)).scalar() or 0
        active_teams = db.query(func.count(func.distinct(PromptLogModel.team_id))).scalar() or 0

        return AnalyticsSummaryResponse(
            total_teams=total_teams,
            total_documents=total_documents,
            total_prompts=total_prompts,
            active_users_today=active_teams
        )

    @staticmethod
    def get_prompt_logs(db: Session, limit: int = 100) -> List[PromptLogModel]:
        """Retrieves recent prompt logs across all teams.

        Args:
            db: Database session.
            limit: Maximum records to return.

        Returns:
            List[PromptLogModel]: List of prompt log entries.
        """
        return db.query(PromptLogModel).order_by(PromptLogModel.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_system_events(db: Session, limit: int = 100) -> List[EventModel]:
        """Retrieves recent system events.

        Args:
            db: Database session.
            limit: Maximum records to return.

        Returns:
            List[EventModel]: List of event records.
        """
        return db.query(EventModel).order_by(EventModel.timestamp.desc()).limit(limit).all()

    @staticmethod
    def log_event(db: Session, team_id: Optional[int], event_type: str, details: Optional[str] = None) -> EventModel:
        """Records a system audit event.

        Args:
            db: Database session.
            team_id: Associated team ID if applicable.
            event_type: Event classification string.
            details: Additional context details.

        Returns:
            EventModel: Persisted event record.
        """
        event = EventModel(team_id=team_id, event_type=event_type, details=details)
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"System Event Logged: [{event_type}] for Team ID {team_id}")
        return event

    @staticmethod
    def log_prompt(db: Session, team_id: int, prompt: str, response: Optional[str], status_code: int = 200) -> PromptLogModel:
        """Logs an API prompt query attempt.

        Args:
            db: Database session.
            team_id: Submitting team ID.
            prompt: Query text.
            response: Response payload text.
            status_code: HTTP response status code.

        Returns:
            PromptLogModel: Persisted log record.
        """
        prompt_log = PromptLogModel(
            team_id=team_id,
            prompt=prompt,
            response=response,
            status_code=status_code
        )
        db.add(prompt_log)
        db.commit()
        db.refresh(prompt_log)
        return prompt_log
