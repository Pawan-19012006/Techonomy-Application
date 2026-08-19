"""API router handling Team arena entry, team details, and prompt history endpoints."""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.team import PromptLogResponse, TeamJoinRequest, TeamResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("/join", response_model=TeamResponse, status_code=status.HTTP_200_OK, summary="Join or Enter Arena")
async def join_team(
    payload: TeamJoinRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TeamResponse:
    """Joins or registers an event team.

    Behavior:
        - If team does not exist: Creates the team, records started_at, and returns team info.
        - If team already exists: Returns existing team record without duplicate creation.
    """
    team = TeamService.join_team(
        db=db,
        team_name=payload.team_name,
        member_names=payload.member_names,
    )
    remaining = TeamService.get_timer_remaining_seconds(team.started_at)
    quota = TeamService.get_or_create_team_quota(db, team.team_name)
    used = quota.questions_used
    limit = quota.question_limit
    return TeamResponse(
        team_name=team.team_name,
        member_names=team.member_names,
        started_at=team.started_at,
        timer_remaining_seconds=remaining,
        session_duration_seconds=7200,
        is_expired=remaining <= 0,
        question_limit=limit,
        questions_used=used,
        questions_remaining=max(0, limit - used),
    )


@router.get("/{team_name}", response_model=TeamResponse, summary="Get Team Info")
async def get_team(
    team_name: str,
    db: Annotated[Session, Depends(get_db)],
) -> TeamResponse:
    """Retrieves team information including member names, started_at timestamp, and persistent team quota."""
    team = TeamService.get_team(db=db, team_name=team_name)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{team_name}' not found.",
        )
    remaining = TeamService.get_timer_remaining_seconds(team.started_at)
    quota = TeamService.get_or_create_team_quota(db, team.team_name)
    used = quota.questions_used
    limit = quota.question_limit
    return TeamResponse(
        team_name=team.team_name,
        member_names=team.member_names,
        started_at=team.started_at,
        timer_remaining_seconds=remaining,
        session_duration_seconds=7200,
        is_expired=remaining <= 0,
        question_limit=limit,
        questions_used=used,
        questions_remaining=max(0, limit - used),
    )


@router.get("/{team_name}/prompts", response_model=List[PromptLogResponse], summary="Get Team Prompt History")
async def get_team_prompts(
    team_name: str,
    db: Annotated[Session, Depends(get_db)],
) -> List[PromptLogResponse]:
    """Retrieves all prompt logs submitted by a specific team."""
    team = TeamService.get_team(db=db, team_name=team_name)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{team_name}' not found.",
        )

    prompts = TeamService.get_team_prompts(db=db, team_name=team_name)
    return [
        PromptLogResponse(
            id=p.id,
            prompt=p.prompt,
            response=p.response,
            created_at=p.created_at,
        )
        for p in prompts
    ]
