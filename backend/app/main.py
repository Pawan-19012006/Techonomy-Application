"""Main FastAPI Application Entrypoint with lifespan pre-warming, health probes, and CORS."""

from contextlib import asynccontextmanager
from pathlib import Path
import time
from typing import Any, Dict, Generator
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import chat, teams
from app.config import settings
from app.database.db import get_db, init_db
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

    # Initialize database tables
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


@app.get("/api/status", tags=["Health"], summary="API Status Endpoint")
async def api_status() -> Dict[str, str]:
    """API status endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
    }


@app.get("/health", tags=["Health"], summary="Health Check Endpoint")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Health check endpoint verifying Backend, Database, Qdrant, Model, and Caches status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        db_status = f"unhealthy: {str(e)}"

    qdrant_status = "healthy"
    try:
        from app.knowledge.indexing.qdrant_client import QdrantClientWrapper
        if not QdrantClientWrapper().health_check():
            qdrant_status = "unhealthy"
    except Exception as e:
        logger.warning(f"Health check Qdrant probe failed: {e}")
        qdrant_status = f"unhealthy: {str(e)}"

    model_loaded = EmbeddingGenerator._model_instance is not None
    overall_healthy = (db_status == "healthy") and model_loaded and (qdrant_status == "healthy")

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "backend": "healthy",
        "database": db_status,
        "qdrant": qdrant_status,
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


# Locate Frontend Production Build / Static Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
ALT_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

DIST_DIR = (
    FRONTEND_DIST_DIR
    if FRONTEND_DIST_DIR.is_dir()
    else (ALT_STATIC_DIR if ALT_STATIC_DIR.is_dir() else None)
)

if DIST_DIR and (DIST_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_or_static(full_path: str):
    """Serves production frontend static assets and handles SPA fallback for client-side routing."""
    clean_path = full_path.lstrip("/")
    if (
        clean_path == "api"
        or clean_path.startswith("api/")
        or clean_path == "health"
        or clean_path.startswith("health/")
        or clean_path == "docs"
        or clean_path.startswith("docs/")
        or clean_path == "openapi.json"
        or clean_path == "redoc"
    ):
        raise HTTPException(status_code=404, detail="API endpoint not found")

    if DIST_DIR:
        if clean_path:
            file_path = DIST_DIR / clean_path
            if file_path.is_file():
                return FileResponse(str(file_path))

        index_path = DIST_DIR / "index.html"
        if index_path.is_file():
            return FileResponse(str(index_path))

    if not clean_path:
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "online",
        }

    raise HTTPException(status_code=404, detail="Resource not found")

