from contextlib import asynccontextmanager
from typing import Any, Dict, Generator
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import chat, teams
from app.config import settings
from app.database.sqlite import get_db, init_db
from app.middleware.exception_handler import global_exception_handler
from app.middleware.logging import RequestLoggingMiddleware
from app.utils.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> Generator[None, None, None]:
    """Application lifespan manager initializing database tables on startup."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    init_db()
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


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
    """Health check endpoint verifying Backend and Database status."""
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Health check DB probe failed: {e}")
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "backend": "healthy",
        "database": db_status,
        "configuration": "loaded",
        "version": settings.VERSION,
    }
