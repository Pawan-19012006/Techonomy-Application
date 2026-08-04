from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.database.models import PromptLogModel, TeamModel
from app.schemas.team import TeamQuestionMetricsResponse, TeamUsageResponse


class TeamService:
    """Service handling Team information, history, and usage metrics."""

    @staticmethod
    def get_team_by_id(db: Session, team_id: int) -> Optional[TeamModel]:
        """Retrieves a Team by ID.

        Args:
            db: Database session.
            team_id: Primary key ID of the team.

        Returns:
            Optional[TeamModel]: Database record or None.
        """
        return db.query(TeamModel).filter(TeamModel.id == team_id).first()

    @staticmethod
    def get_team_usage(team: TeamModel) -> TeamUsageResponse:
        """Calculates remaining questions and usage metrics for a Team.

        Args:
            team: Team database instance.

        Returns:
            TeamUsageResponse: Usage statistics.
        """
        remaining = max(0, team.question_limit - team.questions_used)
        return TeamUsageResponse(
            team_id=team.id,
            question_limit=team.question_limit,
            questions_used=team.questions_used,
            remaining_questions=remaining
        )

    @staticmethod
    def get_team_questions(team: TeamModel) -> TeamQuestionMetricsResponse:
        """Returns question limit, used, and remaining metrics for a Team.

        Args:
            team: Team database instance.

        Returns:
            TeamQuestionMetricsResponse: Breakdown of question quota.
        """
        remaining = max(0, team.question_limit - team.questions_used)
        return TeamQuestionMetricsResponse(
            question_limit=team.question_limit,
            questions_used=team.questions_used,
            questions_remaining=remaining
        )

    @staticmethod
    def get_team_history(db: Session, team_id: int, limit: int = 100) -> Tuple[List[PromptLogModel], int]:
        """Retrieves query prompt execution history for a Team.

        Args:
            db: Database session.
            team_id: Team ID.
            limit: Query return limit.

        Returns:
            Tuple[List[PromptLogModel], int]: List of prompt log entries and total count.
        """
        query = db.query(PromptLogModel).filter(PromptLogModel.team_id == team_id)
        total = query.count()
        logs = query.order_by(PromptLogModel.created_at.desc()).limit(limit).all()
        return logs, total

    @staticmethod
    def list_all_teams(db: Session) -> List[TeamModel]:
        """Lists all registered Teams in the system (Admin operation).

        Args:
            db: Database session.

        Returns:
            List[TeamModel]: List of all teams.
        """
        return db.query(TeamModel).order_by(TeamModel.created_at.desc()).all()
