from datetime import datetime
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models import AuditLogModel, DocumentModel, PromptLogModel, TeamModel
from app.schemas.admin import AnalyticsSummaryResponse
from app.utils.logging import logger


class AnalyticsService:
    """Service providing aggregate usage metrics, prompt log filtering, and audit tracking."""

    @staticmethod
    def get_analytics_summary(db: Session) -> AnalyticsSummaryResponse:
        """Computes comprehensive competition platform analytics.

        Args:
            db: Database session.

        Returns:
            AnalyticsSummaryResponse: Platform metrics summary.
        """
        total_teams = db.query(func.count(TeamModel.id)).scalar() or 0
        active_teams = db.query(func.count(func.distinct(PromptLogModel.team_id))).scalar() or 0

        total_limit = db.query(func.sum(TeamModel.question_limit)).scalar() or 0
        questions_used = db.query(func.sum(TeamModel.questions_used)).scalar() or 0
        questions_remaining = max(0, total_limit - questions_used)

        total_prompts = db.query(func.count(PromptLogModel.id)).scalar() or 0
        avg_response_time = db.query(func.avg(PromptLogModel.response_time_ms)).scalar() or 0.0

        # Determine most active team name
        most_active_result = (
            db.query(TeamModel.name, func.count(PromptLogModel.id).label("prompt_count"))
            .join(PromptLogModel, TeamModel.id == PromptLogModel.team_id)
            .group_by(TeamModel.id)
            .order_by(func.count(PromptLogModel.id).desc())
            .first()
        )
        most_active_team = most_active_result[0] if most_active_result else "N/A"

        # Determine most used document (Placeholder until document usage tracking is integrated)
        most_used_doc_record = db.query(DocumentModel).order_by(DocumentModel.uploaded_at.desc()).first()
        most_used_document = most_used_doc_record.filename if most_used_doc_record else "N/A"

        return AnalyticsSummaryResponse(
            total_teams=total_teams,
            active_teams=active_teams,
            questions_used=int(questions_used),
            questions_remaining=int(questions_remaining),
            total_prompts=total_prompts,
            average_response_time_ms=round(float(avg_response_time), 2),
            most_active_team=most_active_team,
            most_used_document=most_used_document
        )

    @staticmethod
    def get_prompt_logs(
        db: Session,
        team_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100
    ) -> List[PromptLogModel]:
        """Retrieves filtered prompt logs for administration.

        Args:
            db: Database session.
            team_id: Optional filter by team ID.
            date_from: Optional filter for minimum created timestamp.
            date_to: Optional filter for maximum created timestamp.
            limit: Maximum records to return.

        Returns:
            List[PromptLogModel]: Filtered list of prompt log entries.
        """
        query = db.query(PromptLogModel)

        if team_id is not None:
            query = query.filter(PromptLogModel.team_id == team_id)

        if date_from is not None:
            query = query.filter(PromptLogModel.created_at >= date_from)

        if date_to is not None:
            query = query.filter(PromptLogModel.created_at <= date_to)

        return query.order_by(PromptLogModel.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_system_events(db: Session, limit: int = 100) -> List[AuditLogModel]:
        """Retrieves recent system audit logs.

        Args:
            db: Database session.
            limit: Maximum records to return.

        Returns:
            List[AuditLogModel]: List of audit log records.
        """
        return db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc()).limit(limit).all()

    @staticmethod
    def log_event(db: Session, team_id: Optional[int], event_type: str, details: Optional[str] = None) -> AuditLogModel:
        """Records a system audit log entry.

        Args:
            db: Database session.
            team_id: Associated team ID if applicable.
            event_type: Event type string.
            details: Context details.

        Returns:
            AuditLogModel: Persisted log record.
        """
        event = AuditLogModel(team_id=team_id, event_type=event_type, details=details)
        db.add(event)
        db.commit()
        db.refresh(event)
        logger.info(f"System Audit Log: [{event_type}] for Team ID {team_id}")
        return event

    @staticmethod
    def log_prompt(
        db: Session,
        team_id: int,
        prompt: str,
        response: Optional[str],
        status_code: int = 200,
        response_time_ms: float = 0.0
    ) -> PromptLogModel:
        """Logs a user prompt query attempt with execution timing.

        Args:
            db: Database session.
            team_id: Submitting team ID.
            prompt: Query text.
            response: Response payload text.
            status_code: HTTP status code.
            response_time_ms: Processing duration in milliseconds.

        Returns:
            PromptLogModel: Persisted log record.
        """
        prompt_log = PromptLogModel(
            team_id=team_id,
            prompt=prompt,
            response=response,
            status_code=status_code,
            response_time_ms=response_time_ms
        )
        db.add(prompt_log)
        db.commit()
        db.refresh(prompt_log)
        return prompt_log
