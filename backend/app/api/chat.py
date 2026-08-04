from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_team
from app.database.models import TeamModel
from app.database.sqlite import get_db
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.analytics import AnalyticsService
from app.services.rate_limit import RateLimiterService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/query", response_model=ChatQueryResponse)
async def process_chat_query(
    payload: ChatQueryRequest,
    current_team: Annotated[TeamModel, Depends(get_current_team)],
    db: Annotated[Session, Depends(get_db)]
) -> ChatQueryResponse:
    """Processes a user prompt query (Placeholder endpoint without AI processing).

    Validates quota, consumes 1 usage token, logs the prompt, and returns a placeholder response.
    """
    # Verify rate limit / question quota
    RateLimiterService.verify_quota(current_team)

    # Consume quota
    RateLimiterService.consume_quota(db, current_team)

    placeholder_response = (
        f"Received query: '{payload.query}'. "
        "Backend foundation layer active. AI/RAG engine pending implementation."
    )

    # Audit log prompt
    AnalyticsService.log_prompt(
        db=db,
        team_id=current_team.id,
        prompt=payload.query,
        response=placeholder_response,
        status_code=200
    )

    return ChatQueryResponse(
        query=payload.query,
        response=placeholder_response
    )
