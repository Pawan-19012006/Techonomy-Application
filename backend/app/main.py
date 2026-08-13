"""Main FastAPI Application Entrypoint with lifespan pre-warming, health probes, and CORS."""

from contextlib import asynccontextmanager
import time
from typing import Any, Dict, Generator
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import chat, teams
from app.config import settings
from app.database.sqlite import get_db, init_db
from app.knowledge.indexing.embedder import EmbeddingGenerator
from app.knowledge.rag.answer_cache import answer_cache
from app.knowledge.rag.llm_gateway import close_shared_clients
from app.knowledge.retrieval.query_embedding_cache import query_embedding_cache
from app.middleware.exception_handler import global_exception_handler
from app.middleware.logging import RequestLoggingMiddleware
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, None, None]:
    """Application lifespan manager initializing database tables and pre-warming embedding model on startup."""
    t0 = time.perf_counter()
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")

    # Initialize SQLite database tables
    init_db()

    # Preload and warm up SentenceTransformer embedding model in memory
    try:
        logger.info("[STARTUP] Pre-loading and warming up embedding model...")
        EmbeddingGenerator.preload_model(model_name=settings.EMBEDDING_MODEL_NAME)
    except Exception as e:
        logger.error(f"[STARTUP WARNING] Could not pre-load embedding model: {e}")

    startup_time = time.perf_counter() - t0
    logger.info(f"[STARTUP COMPLETE] Application initialized successfully in {startup_time:.3f}s.")

    yield

    # Clean shutdown of HTTP connection pools
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    await close_shared_clients()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Attach CORS Middleware for development & production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "*"],
)

# Attach Custom Logging and Global Exception Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_exception_handler(Exception, global_exception_handler)

# Include Event API Routers under settings.API_PREFIX
app.include_router(teams.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Health"], summary="Root Status Endpoint")
async def root() -> Dict[str, str]:
    """Root status endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
    }


@app.get("/health", tags=["Health"], summary="Health Check Endpoint")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Health check endpoint verifying Backend, Database, Model, and Caches status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        db_status = f"unhealthy: {str(e)}"

    model_loaded = EmbeddingGenerator._model_instance is not None

    return {
        "status": "healthy" if db_status == "healthy" and model_loaded else "degraded",
        "backend": "healthy",
        "database": db_status,
        "embedding_model": {
            "name": settings.EMBEDDING_MODEL_NAME,
            "status": "loaded" if model_loaded else "unloaded",
            "load_time_seconds": round(EmbeddingGenerator._load_time_seconds, 3),
        },
        "caches": {
            "query_embedding_cache": query_embedding_cache.metrics(),
            "answer_cache": answer_cache.metrics(),
        },
        "configuration": "loaded",
        "version": settings.VERSION,
    }
