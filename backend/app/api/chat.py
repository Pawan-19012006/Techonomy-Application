"""API router handling RAG chat requests, team prompt logging, and explicit step instrumentation."""

import time
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.sqlite import get_db
from app.knowledge.rag.chat_service import ChatService
from app.schemas.chat import ChatQueryRequest, ChatResponse
from app.services.team_service import TeamService
from app.utils.logging import logger

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse, summary="Submit RAG Chat Question")
@router.post("/query", response_model=ChatResponse, summary="Submit RAG Chat Question")
async def process_chat_query(
    payload: ChatQueryRequest,
    db: Annotated[Session, Depends(get_db)],
) -> ChatResponse:
    """Executes RAG chat pipeline and records prompt log with explicit milestone logging."""
    t_req_start = time.perf_counter()
    logger.info("==========================================")
    logger.info("[RAG STEP] CHAT REQUEST START")

    question_text = payload.get_question_text()
    if not question_text:
        logger.error("[RAG STEP] CHAT REQUEST FAILED: Empty question text.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question text cannot be empty.",
        )

    requested_team_name = (payload.team_name or "TEAM-01").strip()
    logger.info(f"[RAG STEP] QUERY: '{question_text}' | TEAM: '{requested_team_name}'")

    # Team resolution
    team = TeamService.get_team(db=db, team_name=requested_team_name)
    if not team:
        team = TeamService.join_team(db=db, team_name=requested_team_name, member_names=[requested_team_name])

    active_team_name = str(team.team_name)
    t_validation = time.perf_counter() - t_req_start

    chat_service = ChatService()

    try:
        # Execute ChatService RAG pipeline
        chat_result = await chat_service.ask_async(query=question_text)

        # Database prompt log milestone
        logger.info("[RAG STEP] PROMPT LOG START")
        t_log_start = time.perf_counter()
        TeamService.log_prompt(
            db=db,
            team_name=active_team_name,
            prompt=question_text,
            response=chat_result.answer,
        )
        t_logging = time.perf_counter() - t_log_start
        logger.info(f"[RAG STEP] PROMPT LOG END (Duration: {t_logging:.3f}s)")

        if t_logging > 0.100:
            logger.warning(
                f"[DATABASE TIMING WARNING] PromptLog write for Team '{active_team_name}' "
                f"took {t_logging:.3f}s (>100ms threshold)!"
            )

        t_total = time.perf_counter() - t_req_start
        logger.info(f"[RAG STEP] CHAT REQUEST END (Total Request Time: {t_total:.3f}s)")

        qp = chat_result.timing.get("query_processing", 0.0)
        emb = chat_result.timing.get("embedding", 0.0)
        vsearch = chat_result.timing.get("vector_search", 0.0)
        rerank = chat_result.timing.get("reranking", 0.0)
        ctx = chat_result.timing.get("context_building", 0.0)
        pb = chat_result.timing.get("prompt_building", 0.0)
        llm = chat_result.timing.get("llm_generation", 0.0)

        timing_log = (
            f"\n[RAG TIMING BREAKDOWN]\n"
            f"validation={t_validation:.3f}s\n"
            f"query_processing={qp:.3f}s\n"
            f"embedding={emb:.3f}s\n"
            f"vector_search={vsearch:.3f}s\n"
            f"reranking={rerank:.3f}s\n"
            f"context_building={ctx:.3f}s\n"
            f"prompt_building={pb:.3f}s\n"
            f"llm_generation={llm:.3f}s\n"
            f"logging={t_logging:.3f}s\n"
            f"total={t_total:.3f}s\n"
            f"=========================================="
        )
        logger.info(timing_log)

        return ChatResponse(
            answer=chat_result.answer,
            sources=chat_result.sources,
            team_name=active_team_name,
        )

    except Exception as e:
        logger.error(f"[RAG STEP] CHAT REQUEST FAILED for Team '{active_team_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation failed: {str(e)}",
        ) from e
