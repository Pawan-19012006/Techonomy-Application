"""API router handling RAG chat requests, streaming responses, asynchronous prompt logging, and request observability."""

import json
import time
import uuid
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.sqlite import SessionLocal, get_db
from app.knowledge.rag.chat_service import ChatService
from app.knowledge.rag.llm_gateway import LLMGateway
from app.schemas.chat import ChatQueryRequest, ChatResponse
from app.services.team_service import TeamService
from app.utils.logging import logger

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
) -> ChatResponse:
    """Executes RAG chat pipeline and schedules background prompt logging for low-latency HTTP responses."""
    request_id = str(uuid.uuid4())[:8]
    t_req_start = time.perf_counter()
    logger.info(f"========================================== [REQ ID: {request_id}]")
    logger.info(f"[RAG STEP] CHAT REQUEST START (req_id={request_id})")

    question_text = payload.get_question_text()
    if not question_text:
        logger.error(f"[RAG STEP] CHAT REQUEST FAILED (req_id={request_id}): Empty question text.")
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

        # Schedule asynchronous database prompt logging as FastAPI BackgroundTask
        background_tasks.add_task(
            _async_log_prompt,
            team_name=active_team_name,
            prompt=question_text,
            response=chat_result.answer,
        )

        t_total = time.perf_counter() - t_req_start

        qp = chat_result.timing.get("query_processing", 0.0)
        emb = chat_result.timing.get("embedding", 0.0)
        vsearch = chat_result.timing.get("vector_search", 0.0)
        rerank = chat_result.timing.get("reranking", 0.0)
        ctx = chat_result.timing.get("context_building", 0.0)
        pb = chat_result.timing.get("prompt_building", 0.0)
        llm = chat_result.timing.get("llm_generation", 0.0)

        timing_log = (
            f"\n[RAG TIMING BREAKDOWN] (request_id={request_id})\n"
            f"validation={t_validation:.4f}s\n"
            f"query_processing={qp:.4f}s\n"
            f"embedding={emb:.4f}s\n"
            f"vector_search={vsearch:.4f}s\n"
            f"reranking={rerank:.4f}s\n"
            f"context_building={ctx:.4f}s\n"
            f"prompt_building={pb:.4f}s\n"
            f"llm_generation={llm:.4f}s\n"
            f"logging_async=true\n"
            f"total={t_total:.4f}s\n"
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


@router.post("/stream", summary="Submit RAG Chat Question with Streaming Response")
async def stream_chat_query(
    payload: ChatQueryRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
):
    """Executes RAG retrieval and streams tokens as Server-Sent Events (SSE)."""
    question_text = payload.get_question_text()
    if not question_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question text cannot be empty.",
        )

    requested_team_name = (payload.team_name or "TEAM-01").strip()
    team = TeamService.get_team(db=db, team_name=requested_team_name)
    if not team:
        team = TeamService.join_team(db=db, team_name=requested_team_name, member_names=[requested_team_name])

    active_team_name = str(team.team_name)
    chat_service = ChatService()

    async def event_generator():
        # Retrieve context
        retrieval_result = chat_service.retrieval_pipeline.retrieve(query=question_text)
        sources = chat_service._extract_sources(retrieval_result)
        prompt = chat_service.prompt_builder.build_prompt(
            query=question_text,
            chunks=retrieval_result.reranked_results,
        )

        gateway = LLMGateway()
        full_answer = []

        # Yield SSE tokens
        async for token in gateway.generate_stream_async(prompt):
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

    return StreamingResponse(event_generator(), media_type="text/event-stream")
