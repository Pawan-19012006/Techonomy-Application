from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.team import TeamResponse, TeamUsageResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/me", response_model=TeamResponse)
async def get_team_info(
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> TeamModel:
    """Returns details for the currently authenticated Team."""
    return current_team


@router.get("/usage", response_model=TeamUsageResponse)
async def get_team_usage(
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> TeamUsageResponse:
    """Returns question limit and usage metrics for the authenticated Team."""
    return TeamService.get_team_usage(current_team)
