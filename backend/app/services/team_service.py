"""Service handling team registration, arena entry, and prompt log tracking."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import PromptLogModel, TeamModel, utc_now
from app.utils.logging import logger


class TeamService:
    """Service isolating team arena management and prompt log database operations."""

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
        db.commit()
        db.refresh(new_team)
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
    def log_prompt(db: Session, team_name: str, prompt: str, response: str) -> PromptLogModel:
        """Records a successful RAG prompt log entry associated with a team.

        Args:
            db: Database session.
            team_name: Submitting team name.
            prompt: User question prompt.
            response: RAG response text.

        Returns:
            PromptLogModel: Persisted prompt log record.
        """
        log_entry = PromptLogModel(
            team_name=team_name.strip(),
            prompt=prompt,
            response=response,
            created_at=utc_now(),
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logger.info(f"Logged prompt entry #{log_entry.id} for Team '{team_name}'")
        return log_entry
