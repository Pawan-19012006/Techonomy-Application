from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.database.models import TeamModel
from app.utils.logging import logger


class RateLimiterService:
    """Service enforcing team question quotas and rate limits."""

    @staticmethod
    def verify_quota(team: TeamModel) -> None:
        """Verifies if the team has available questions in their quota.

        Raises:
            HTTPException: 429 Too Many Requests if quota is exhausted.
        """
        if team.questions_used >= team.question_limit:
            logger.warning(
                f"Quota exceeded for Team '{team.name}' (ID: {team.id}). "
                f"Used: {team.questions_used}/{team.question_limit}."
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Question quota limit reached ({team.question_limit} questions allowed)."
            )

    @staticmethod
    def consume_quota(db: Session, team: TeamModel) -> TeamModel:
        """Increments questions_used for a team after a valid query.

        Args:
            db: Database session.
            team: Team database model.

        Returns:
            TeamModel: Updated team record.
        """
        RateLimiterService.verify_quota(team)
        team.questions_used += 1
        db.add(team)
        db.commit()
        db.refresh(team)
        logger.info(
            f"Consumed 1 quota for Team '{team.name}' (ID: {team.id}). "
            f"Remaining: {team.question_limit - team.questions_used}."
        )
        return team
