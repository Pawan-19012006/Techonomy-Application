from typing import Annotated, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.admin import AnalyticsSummaryResponse, PromptLogResponse
from app.schemas.team import TeamResponse
from app.services.analytics import AnalyticsService
from app.services.team_service import TeamService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/teams", response_model=List[TeamResponse])
async def list_all_teams(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> List[TeamResponse]:
    """Retrieves all registered Teams (Administrator permission required)."""
    return TeamService.list_all_teams(db)


@router.get("/logs", response_model=List[PromptLogResponse])
async def view_prompt_logs(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 100
) -> List[PromptLogResponse]:
    """Retrieves system prompt query logs (Administrator permission required)."""
    return AnalyticsService.get_prompt_logs(db, limit)


@router.get("/analytics", response_model=AnalyticsSummaryResponse)
async def view_analytics(
    admin: Annotated[TeamModel, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> AnalyticsSummaryResponse:
    """Retrieves platform analytics summary (Administrator permission required)."""
    return AnalyticsService.get_analytics_summary(db)
