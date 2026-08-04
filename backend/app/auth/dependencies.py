from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import decode_access_token
from app.database.models import TeamModel
from app.database.sqlite import get_db

security = HTTPBearer()


def get_current_team(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)]
) -> TeamModel:
    """FastAPI dependency asserting valid JWT authentication and retrieving Team model.

    Raises:
        HTTPException: 401 Unauthorized if invalid token or missing user.

    Returns:
        TeamModel: Authenticated team database instance.
    """
    token = credentials.credentials
    token_data = decode_access_token(token)

    if token_data is None or token_data.team_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    team = db.query(TeamModel).filter(TeamModel.id == token_data.team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated team account not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return team


def get_current_admin(
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> TeamModel:
    """FastAPI dependency asserting that current team user has administrator permissions.

    Raises:
        HTTPException: 403 Forbidden if not administrator.

    Returns:
        TeamModel: Authenticated admin team database instance.
    """
    if not current_team.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permissions required for this operation"
        )
    return current_team
