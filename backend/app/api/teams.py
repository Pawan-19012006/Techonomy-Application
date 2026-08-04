from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.team import TeamHistoryResponse, TeamQuestionMetricsResponse, TeamResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/me", response_model=TeamResponse, summary="Get Current Team Details")
async def get_team_info(
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> TeamModel:
    """Returns profile information for the currently authenticated Team."""
    return current_team


@router.get("/questions", response_model=TeamQuestionMetricsResponse, summary="Get Team Question Quota Breakdown")
async def get_team_questions(
    current_team: Annotated[TeamModel, Depends(get_current_team)]
) -> TeamQuestionMetricsResponse:
    """Returns question quota, used, and remaining question count for the authenticated Team."""
    return TeamService.get_team_questions(current_team)


@router.get("/history", response_model=TeamHistoryResponse, summary="Get Team Prompt Execution History")
async def get_team_history(
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100
) -> TeamHistoryResponse:
    """Returns prompt query execution history for the authenticated Team."""
    logs, total = TeamService.get_team_history(db, current_team.id, limit=limit)
    return TeamHistoryResponse(logs=logs, total_count=total)
