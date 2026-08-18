"""Admin Control Panel Router for KAIROS Competition Platform."""

from datetime import datetime, timezone
import logging
from typing import Annotated, Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database.db import get_db
from app.database.models import TeamModel, TeamQuotaModel, PromptLogModel, utc_now
from app.services.team_service import TeamService

logger = logging.getLogger("Techonomy")

router = APIRouter(prefix="/admin", tags=["Admin Control Panel"])

# Simple deterministic token verification for admin session
ADMIN_TOKEN_SECRET = f"kairos_admin_token_{settings.ADMIN_SECRET_KEY[:8]}"


class AdminLoginRequest(BaseModel):
    username: str = Field(..., description="Admin Username")
    password: str = Field(..., description="Admin Password")


class AdminLoginResponse(BaseModel):
    access_token: str
    username: str
    role: str = "admin"


def verify_admin_auth(
    authorization: Optional[str] = Header(None),
    x_admin_token: Optional[str] = Header(None),
) -> str:
    """Dependency verifying admin authentication token from Authorization or X-Admin-Token header.
    
    Participant callers will receive HTTP 403 Forbidden.
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif x_admin_token:
        token = x_admin_token

    if not token or token != ADMIN_TOKEN_SECRET:
        logger.warning(f"[SECURITY REJECTION] Unauthorized access attempt to Admin API endpoints.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin authentication required.",
        )
    return settings.ADMIN_USERNAME


@router.post("/login", response_model=AdminLoginResponse, summary="Admin Login")
async def admin_login(payload: AdminLoginRequest) -> AdminLoginResponse:
    """Authenticates event administrator credentials and returns an admin access token."""
    username = payload.username.strip()
    password = payload.password.strip()

    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        logger.info(f"[ADMIN AUTH SUCCESS] Admin '{username}' authenticated successfully.")
        return AdminLoginResponse(
            access_token=ADMIN_TOKEN_SECRET,
            username=settings.ADMIN_USERNAME,
            role="admin",
        )

    logger.warning(f"[ADMIN AUTH FAILURE] Invalid login attempt for username '{username}'.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin credentials.",
    )


@router.get("/overview", summary="Get Event Overview Metrics")
async def get_admin_overview(
    db: Annotated[Session, Depends(get_db)],
    admin_user: str = Depends(verify_admin_auth),
) -> Dict[str, Any]:
    """Returns high-level competition overview statistics across all participating teams."""
    teams = db.query(TeamModel).all()
    quotas = db.query(TeamQuotaModel).all()

    total_registered_teams = len(teams)
    active_teams_count = 0
    total_questions_used = sum(q.questions_used for q in quotas)
    total_questions_remaining = sum(max(0, q.question_limit - q.questions_used) for q in quotas)

    for team in teams:
        if not TeamService.is_session_expired(team.started_at):
            active_teams_count += 1

    return {
        "admin_username": admin_user,
        "registered_teams": total_registered_teams,
        "active_teams": active_teams_count,
        "total_questions_used": total_questions_used,
        "total_questions_remaining": total_questions_remaining,
        "event_status": "LIVE",
        "question_limit_per_team": 10,
    }


@router.get("/teams", summary="Get All Registered Teams with Competition Metrics")
async def get_admin_teams(
    db: Annotated[Session, Depends(get_db)],
    admin_user: str = Depends(verify_admin_auth),
) -> List[Dict[str, Any]]:
    """Returns a list of all registered teams with real-time session and quota metrics."""
    teams = db.query(TeamModel).order_by(TeamModel.started_at.desc()).all()
    results = []

    for team in teams:
        quota = TeamService.get_or_create_team_quota(db=db, team_name=team.team_name)
        
        # Get latest prompt activity timestamp
        last_log = (
            db.query(PromptLogModel)
            .filter(PromptLogModel.team_name == team.team_name)
            .order_by(PromptLogModel.created_at.desc())
            .first()
        )
        last_activity_at = (
            last_log.created_at.isoformat()
            if last_log
            else team.started_at.isoformat()
        )

        # Determine status
        is_expired = TeamService.is_session_expired(team.started_at)
        questions_used = quota.questions_used
        limit = quota.question_limit
        questions_remaining = max(0, limit - questions_used)

        if questions_remaining == 0:
            status_str = "COMPLETED"
        elif is_expired:
            status_str = "TIME_EXPIRED"
        else:
            status_str = "ACTIVE"

        results.append(
            {
                "team_name": team.team_name,
                "member_names": team.member_names,
                "started_at": team.started_at.isoformat() if team.started_at else None,
                "last_activity_at": last_activity_at,
                "questions_used": questions_used,
                "questions_remaining": questions_remaining,
                "question_limit": limit,
                "status": status_str,
            }
        )

    return results


@router.get("/teams/{team_name}", summary="Get Detailed Team Evaluation & Prompt History")
async def get_admin_team_detail(
    team_name: str,
    db: Annotated[Session, Depends(get_db)],
    admin_user: str = Depends(verify_admin_auth),
) -> Dict[str, Any]:
    """Returns detailed team information along with complete prompt/RAG execution history."""
    clean_name = team_name.strip()
    team = TeamService.get_team(db=db, team_name=clean_name)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{clean_name}' not found.",
        )

    quota = TeamService.get_or_create_team_quota(db=db, team_name=clean_name)
    prompt_logs = (
        db.query(PromptLogModel)
        .filter(PromptLogModel.team_name == clean_name)
        .order_by(PromptLogModel.created_at.desc())
        .all()
    )

    is_expired = TeamService.is_session_expired(team.started_at)
    questions_used = quota.questions_used
    limit = quota.question_limit
    questions_remaining = max(0, limit - questions_used)

    if questions_remaining == 0:
        status_str = "COMPLETED"
    elif is_expired:
        status_str = "TIME_EXPIRED"
    else:
        status_str = "ACTIVE"

    prompts_data = []
    for log in prompt_logs:
        prompts_data.append(
            {
                "id": log.id,
                "prompt": log.prompt,
                "response": log.response,
                "sources": log.sources or [],
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return {
        "team_name": team.team_name,
        "member_names": team.member_names,
        "started_at": team.started_at.isoformat() if team.started_at else None,
        "last_activity_at": prompts_data[0]["created_at"] if prompts_data else (team.started_at.isoformat() if team.started_at else None),
        "questions_used": questions_used,
        "questions_remaining": questions_remaining,
        "question_limit": limit,
        "status": status_str,
        "prompts": prompts_data,
    }
