from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse, summary="Get Unified Team Dashboard")
async def get_dashboard(
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)]
) -> DashboardResponse:
    """Returns a unified dashboard payload containing team, event, timer, and document metrics."""
    return DashboardService.get_team_dashboard(db, current_team)
