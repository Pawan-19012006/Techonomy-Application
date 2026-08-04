from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.team import TeamHistoryResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=TeamHistoryResponse, summary="Get Team Query Prompt History")
async def get_history(
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100
) -> TeamHistoryResponse:
    """Returns prompt query history entries for the authenticated Team."""
    logs, total = TeamService.get_team_history(db, current_team.id, limit=limit)
    return TeamHistoryResponse(logs=logs, total_count=total)
