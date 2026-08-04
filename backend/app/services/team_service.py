from typing import List, Optional
from sqlalchemy.orm import Session

from app.database.models import TeamModel
from app.schemas.team import TeamUsageResponse


class TeamService:
    """Service handling Team information and usage metrics."""

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
    def list_all_teams(db: Session) -> List[TeamModel]:
        """Lists all registered Teams in the system (Admin operation).

        Args:
            db: Database session.

        Returns:
            List[TeamModel]: List of all teams.
        """
        return db.query(TeamModel).order_by(TeamModel.created_at.desc()).all()
