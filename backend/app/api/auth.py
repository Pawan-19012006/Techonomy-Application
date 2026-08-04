from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.team import TeamCreate, TeamResponse
from app.services.authentication import AuthenticationService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
    """Authenticates a Team account and returns a JWT access token."""
    token_response = AuthenticationService.authenticate_team(db, login_data)
    if not token_response:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_response


@router.post("/register", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def register(
    team_data: TeamCreate,
    db: Annotated[Session, Depends(get_db)]
) -> TeamResponse:
    """Registers a new Team account."""
    return AuthenticationService.create_team(db, team_data)


@router.get("/me", response_model=TeamResponse)
async def get_me(
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> TeamModel:
    """Returns profile information for the authenticated team."""
    return current_team
