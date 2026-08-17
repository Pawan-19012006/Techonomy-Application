"""API router handling RAG chat requests, streaming responses, asynchronous prompt logging, and request observability."""

import json
import time
import uuid
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.db import SessionLocal, get_db
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.llm_gateway import LLMGateway
from app.schemas.chat import ChatQueryRequest, ChatResponse
from app.services.team_service import TeamService
from app.utils.logging import logger
from app.utils.observability import LatencyTracker

router = APIRouter(prefix="/chat", tags=["Chat"])


def _async_log_prompt(team_name: str, prompt: str, response: str) -> None:
    """FastAPI BackgroundTask helper that writes prompt log asynchronously without blocking HTTP response."""
    db = SessionLocal()
    try:
        t0 = time.perf_counter()
        TeamService.log_prompt(
            db=db,
            team_name=team_name,
            prompt=prompt,
            response=response,
        )
        duration = time.perf_counter() - t0
        logger.info(f"[ASYNC PERSISTENCE] Logged prompt entry for Team '{team_name}' in {duration:.4f}s.")
    except Exception as e:
        logger.error(f"[ASYNC PERSISTENCE FAILED] Could not log prompt for Team '{team_name}': {e}")
    finally:
        db.close()


@router.post("", response_model=ChatResponse, summary="Submit RAG Chat Question")
@router.post("/query", response_model=ChatResponse, summary="Submit RAG Chat Question")
async def process_chat_query(
    payload: ChatQueryRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    request: Request = None,
) -> ChatResponse:
    """Executes RAG chat pipeline and schedules background prompt logging for low-latency HTTP responses."""
    req_id = getattr(getattr(request, "state", None), "request_id", None) or str(uuid.uuid4())[:8]
    tracker = LatencyTracker(request_id=req_id)
    t_req_start = time.perf_counter()
    logger.info(f"========================================== [REQ ID: {req_id}]")
    logger.info(f"[RAG STEP] CHAT REQUEST START (req_id={req_id})")

    question_text = payload.get_question_text()
    if not question_text:
        logger.error(f"[RAG STEP] CHAT REQUEST FAILED (req_id={req_id}): Empty question text.")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question text cannot be empty.",
        )

    requested_team_name = (payload.team_name or "TEAM-01").strip()
    logger.info(f"[RAG STEP] QUERY: '{question_text}' | TEAM: '{requested_team_name}'")

    # Team resolution with timing
    t_db0 = time.perf_counter()
    team = TeamService.get_team(db=db, team_name=requested_team_name)
    if not team:
        team = TeamService.join_team(db=db, team_name=requested_team_name, member_names=[requested_team_name])
    t_db_team = (time.perf_counter() - t_db0) * 1000.0
    tracker.record_db_team_lookup(t_db_team)

    active_team_name = str(team.team_name)

    # 1. Atomically reserve team prompt quota with timing
    t_db1 = time.perf_counter()
    reserved = TeamService.reserve_team_quota(db=db, team_name=active_team_name)
    t_db_quota = (time.perf_counter() - t_db1) * 1000.0
    tracker.record_db_quota_reservation(t_db_quota, reserved=reserved)

    if not reserved:
        logger.warning(f"[QUOTA EXCEEDED] Team '{active_team_name}' exceeded prompt question limit.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Team prompt question limit reached for this event.",
        )

    t_validation = time.perf_counter() - t_req_start

    chat_service = ChatService()

    try:
        # Execute ChatService RAG pipeline
        chat_result = await chat_service.ask_async(
            query=question_text,
            request_id=req_id,
            tracker=tracker,
        )

        # Schedule asynchronous database prompt logging as FastAPI BackgroundTask
        background_tasks.add_task(
            _async_log_prompt,
            team_name=active_team_name,
            prompt=question_text,
            response=chat_result.answer,
        )

        t_total_ms = (time.perf_counter() - t_req_start) * 1000.0
        tracker.emit_summary(rag_total_ms=t_total_ms)

        return ChatResponse(
            answer=chat_result.answer,
            sources=chat_result.sources,
            team_name=active_team_name,
        )

    except Exception as e:
        # Check if pre-generation LLM acquisition failed -> Roll back team prompt quota
        from app.knowledge.exceptions import LLMQuotaExhaustedError
        if isinstance(e, (LLMQuotaExhaustedError, ChatServiceError)) and "LLMQuotaExhaustedError" in str(e):
            logger.warning(f"[PRE-GENERATION ROLLBACK] Rolling back quota for Team '{active_team_name}' due to lane acquisition failure: {e}")
            TeamService.rollback_team_quota(db=db, team_name=active_team_name)

        logger.error(f"[RAG STEP] CHAT REQUEST FAILED for Team '{active_team_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat generation failed: {str(e)}",
        ) from e


@router.post("/stream", summary="Submit RAG Chat Question with Streaming Response")
async def stream_chat_query(
    payload: ChatQueryRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    request: Request = None,
):
    """Executes RAG retrieval and streams tokens as Server-Sent Events (SSE)."""
    req_id = getattr(getattr(request, "state", None), "request_id", None) or str(uuid.uuid4())[:8]
    tracker = LatencyTracker(request_id=req_id)
    t_req_start = time.perf_counter()

    question_text = payload.get_question_text()
    if not question_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question text cannot be empty.",
        )

    requested_team_name = (payload.team_name or "TEAM-01").strip()

    t_db0 = time.perf_counter()
    team = TeamService.get_team(db=db, team_name=requested_team_name)
    if not team:
        team = TeamService.join_team(db=db, team_name=requested_team_name, member_names=[requested_team_name])
    tracker.record_db_team_lookup((time.perf_counter() - t_db0) * 1000.0)

    active_team_name = str(team.team_name)

    # 1. Atomically reserve team prompt quota
    t_db1 = time.perf_counter()
    reserved = TeamService.reserve_team_quota(db=db, team_name=active_team_name)
    tracker.record_db_quota_reservation((time.perf_counter() - t_db1) * 1000.0, reserved=reserved)

    if not reserved:
        logger.warning(f"[QUOTA EXCEEDED] Team '{active_team_name}' exceeded prompt question limit.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Team prompt question limit reached for this event.",
        )

    chat_service = ChatService()

    async def event_generator():
        try:
            # Retrieve context
            retrieval_result = chat_service.retrieval_pipeline.retrieve(
                query=question_text,
                request_id=req_id,
                tracker=tracker,
            )
            sources = chat_service._extract_sources(retrieval_result)
            prompt = chat_service.prompt_builder.build_prompt(
                query=question_text,
                chunks=retrieval_result.reranked_results,
            )

            gateway = LLMGateway()
            full_answer = []

            # Yield SSE tokens
            async for token in gateway.generate_stream_async(prompt, request_id=req_id, tracker=tracker):
                full_answer.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

            complete_text = "".join(full_answer)

            # Schedule background logging
            background_tasks.add_task(
                _async_log_prompt,
                team_name=active_team_name,
                prompt=question_text,
                response=complete_text,
            )

            # Emit completion payload with sources
            final_payload = {
                "done": True,
                "sources": [s.model_dump() for s in sources],
                "team_name": active_team_name,
            }
            yield f"data: {json.dumps(final_payload)}\n\n"

            t_total_ms = (time.perf_counter() - t_req_start) * 1000.0
            tracker.emit_summary(rag_total_ms=t_total_ms)

        except Exception as e:
            logger.error(f"[RAG STREAM STEP] STREAMING FAILED for Team '{active_team_name}': {e}")
            yield f"data: {json.dumps({'token': f'\\n[Error: {str(e)}]', 'error': True})}\n\n"
            yield f"data: {json.dumps({'done': True, 'sources': [], 'team_name': active_team_name})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
