"""Service handling team registration, arena entry, and prompt log tracking."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import PromptLogModel, TeamModel, TeamQuotaModel, utc_now
from app.utils.logging import logger


from datetime import datetime, timezone

EVENT_DURATION_SECONDS = 9000  # 2 Hours 30 Minutes competition duration


class TeamService:
    """Service isolating team arena management and prompt log database operations."""

    @staticmethod
    def get_timer_remaining_seconds(started_at: Optional[datetime]) -> int:
        """Computes remaining seconds for a team's 2h 30m competition session."""
        if not started_at:
            return EVENT_DURATION_SECONDS
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        now = utc_now()
        elapsed = (now - started_at).total_seconds()
        remaining = EVENT_DURATION_SECONDS - int(elapsed)
        return max(0, remaining)

    @staticmethod
    def is_session_expired(started_at: Optional[datetime]) -> bool:
        """Returns True if the team's 2h 30m competition session duration has elapsed."""
        return TeamService.get_timer_remaining_seconds(started_at) <= 0

    @staticmethod
    def join_team(db: Session, team_name: str, member_names: List[str]) -> TeamModel:
        """Joins or registers an event team.

        If team already exists, returns the existing record.
        If team does not exist, creates new team record with current timestamp as started_at.

        Args:
            db: Database session.
            team_name: Unique team name identifier.
            member_names: List of member names.

        Returns:
            TeamModel: Created or existing team database record.
        """
        clean_name = team_name.strip()
        existing_team = db.query(TeamModel).filter(TeamModel.team_name == clean_name).first()

        if existing_team:
            logger.info(f"Team '{clean_name}' re-entering arena. Returning existing team record.")
            return existing_team

        logger.info(f"Creating new event team '{clean_name}' with members: {member_names}")
        new_team = TeamModel(
            team_name=clean_name,
            member_names=member_names,
            started_at=utc_now(),
        )
        db.add(new_team)
        try:
            db.commit()
        except Exception:
            db.rollback()
            existing = db.query(TeamModel).filter(TeamModel.team_name == clean_name).first()
            if existing:
                return existing
            raise
        return new_team

    @staticmethod
    def get_team(db: Session, team_name: str) -> Optional[TeamModel]:
        """Retrieves team record by team_name primary key.

        Args:
            db: Database session.
            team_name: Target team name.

        Returns:
            Optional[TeamModel]: Team database record if found, else None.
        """
        return db.query(TeamModel).filter(TeamModel.team_name == team_name.strip()).first()

    @staticmethod
    def get_team_prompts(db: Session, team_name: str) -> List[PromptLogModel]:
        """Retrieves all prompt log entries submitted by a specific team.

        Args:
            db: Database session.
            team_name: Target team name.

        Returns:
            List[PromptLogModel]: List of prompt logs for the team.
        """
        return (
            db.query(PromptLogModel)
            .filter(PromptLogModel.team_name == team_name.strip())
            .order_by(PromptLogModel.created_at.asc())
            .all()
        )

    @staticmethod
    def log_prompt(
        db: Session,
        team_name: str,
        prompt: str,
        response: str,
        sources: Optional[List[dict]] = None,
    ) -> PromptLogModel:
        """Records a successful RAG prompt log entry associated with a team."""
        log_entry = PromptLogModel(
            team_name=team_name.strip(),
            prompt=prompt,
            response=response,
            sources=sources,
            created_at=utc_now(),
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logger.info(f"Logged prompt entry #{log_entry.id} for Team '{team_name}'")
        return log_entry

    @staticmethod
    def get_or_create_team_quota(
        db: Session,
        team_name: str,
        event_id: Optional[int] = None,
        default_limit: int = 10,
    ) -> TeamQuotaModel:
        """Retrieves or creates TeamQuotaModel record for team/event."""
        from sqlalchemy.exc import IntegrityError
        from app.database.models import TeamQuotaModel, EventModel

        clean_name = team_name.strip()

        # Check event default limit if event_id provided
        if event_id is not None:
            evt = db.query(EventModel).filter(EventModel.id == event_id).first()
            if evt:
                default_limit = evt.question_limit

        query = db.query(TeamQuotaModel).filter(TeamQuotaModel.team_name == clean_name)
        if event_id is not None:
            query = query.filter(TeamQuotaModel.event_id == event_id)
        else:
            query = query.filter(TeamQuotaModel.event_id.is_(None))

        existing = query.first()
        if existing:
            return existing

        try:
            new_quota = TeamQuotaModel(
                team_name=clean_name,
                event_id=event_id,
                questions_used=0,
                question_limit=default_limit,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(new_quota)
            db.commit()
            return new_quota
        except IntegrityError:
            db.rollback()
            return query.first()

    @staticmethod
    def reserve_team_quota(
        db: Session,
        team_name: str,
        event_id: Optional[int] = None,
    ) -> bool:
        """Atomically reserves one prompt slot for a team if questions_used < question_limit."""
        from sqlalchemy import update
        from app.database.models import TeamQuotaModel

        clean_name = team_name.strip()
        TeamService.get_or_create_team_quota(db, clean_name, event_id)

        stmt = update(TeamQuotaModel).where(
            TeamQuotaModel.team_name == clean_name,
            TeamQuotaModel.questions_used < TeamQuotaModel.question_limit,
        )
        if event_id is not None:
            stmt = stmt.where(TeamQuotaModel.event_id == event_id)
        else:
            stmt = stmt.where(TeamQuotaModel.event_id.is_(None))

        stmt = stmt.values(
            questions_used=TeamQuotaModel.questions_used + 1,
            updated_at=utc_now(),
        )

        res = db.execute(stmt)
        db.commit()
        return res.rowcount == 1

    @staticmethod
    def rollback_team_quota(
        db: Session,
        team_name: str,
        event_id: Optional[int] = None,
    ) -> bool:
        """Atomically rolls back one prompt slot for a team (questions_used = max(0, questions_used - 1))."""
        from sqlalchemy import update
        from app.database.models import TeamQuotaModel

        clean_name = team_name.strip()
        stmt = update(TeamQuotaModel).where(
            TeamQuotaModel.team_name == clean_name,
            TeamQuotaModel.questions_used > 0,
        )
        if event_id is not None:
            stmt = stmt.where(TeamQuotaModel.event_id == event_id)
        else:
            stmt = stmt.where(TeamQuotaModel.event_id.is_(None))

        stmt = stmt.values(
            questions_used=TeamQuotaModel.questions_used - 1,
            updated_at=utc_now(),
        )

        res = db.execute(stmt)
        db.commit()
        return res.rowcount == 1

