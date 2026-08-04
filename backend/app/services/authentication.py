from typing import Optional
from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.database.models import TeamModel
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.team import TeamCreate
from app.utils.logging import logger


class AuthenticationService:
    """Service handling Team authentication and account management."""

    @staticmethod
    def authenticate_team(db: Session, login_data: LoginRequest) -> Optional[TokenResponse]:
        """Validates credentials and generates a JWT token.

        Args:
            db: Database session.
            login_data: Email and password payload.

        Returns:
            Optional[TokenResponse]: Issued JWT token or None if authentication failed.
        """
        team = db.query(TeamModel).filter(TeamModel.email == login_data.email).first()
        if not team or not verify_password(login_data.password, team.hashed_password):
            logger.warning(f"Failed authentication attempt for email: {login_data.email}")
            return None

        access_token = create_access_token(
            data={"sub": team.email, "team_id": team.id, "is_admin": team.is_admin}
        )
        logger.info(f"Team '{team.name}' (ID: {team.id}) logged in successfully.")
        return TokenResponse(access_token=access_token, token_type="bearer")

    @staticmethod
    def create_team(db: Session, team_data: TeamCreate) -> TeamModel:
        """Registers a new Team in the system.

        Args:
            db: Database session.
            team_data: Registration payload.

        Returns:
            TeamModel: Created team database object.
        """
        hashed_pwd = hash_password(team_data.password)
        new_team = TeamModel(
            name=team_data.name,
            email=team_data.email,
            hashed_password=hashed_pwd,
            question_limit=team_data.question_limit,
            is_admin=team_data.is_admin
        )
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        logger.info(f"Created new Team '{new_team.name}' with ID {new_team.id}.")
        return new_team
