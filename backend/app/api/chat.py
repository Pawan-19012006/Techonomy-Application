"""API router handling RAG chat requests and team prompt logging."""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.sqlite import get_db
from app.knowledge.rag.chat_service import ChatService
from app.schemas.chat import ChatQueryRequest, ChatRequest, ChatResponse
from app.services.team_service import TeamService
from app.utils.logging import logger

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Submit RAG Chat Question")
@router.post("/query", response_model=ChatResponse, summary="Submit RAG Chat Question")
async def process_chat_query(
    payload: ChatQueryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    """Executes RAG chat pipeline and records prompt log for the team.

    Pipeline:
        1. Extract team_name and question text.
        2. Verify team exists (auto-register if missing).
        3. Call ChatService.ask_async() -> Retrieval + Prompt Building + LLM Generation.
        4. Store prompt log in prompt_logs table.
        5. Return ChatResponse JSON (answer, sources, team_name).
    """
    question_text = payload.get_question_text()
    if not question_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question text cannot be empty.",
        )

    team_name = (payload.team_name or "TEAM-01").strip()

    # Ensure team exists or auto-join
    team = TeamService.get_team(db=db, team_name=team_name)
    if not team:
        team = TeamService.join_team(db=db, team_name=team_name, member_names=[team_name])

    chat_service = ChatService()

    try:
        # Step 3: Execute ChatService RAG pipeline
        chat_result = await chat_service.ask_async(query=question_text)

        # Step 4: Record prompt log in SQLite database
        TeamService.log_prompt(
            db=db,
            team_name=team.team_name,
            prompt=question_text,
            response=chat_result.answer,
        )

        # Step 5: Return ChatResponse
        return ChatResponse(
            answer=chat_result.answer,
            sources=chat_result.sources,
            team_name=team.team_name,
        )

    except Exception as e:
        logger.error(f"Chat processing failed for Team '{team_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation failed: {str(e)}",
        ) from e
