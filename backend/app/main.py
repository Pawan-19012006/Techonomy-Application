from contextlib import asynccontextmanager
from typing import Any, Dict, Generator
from fastapi import Depends, FastAPI, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import admin, auth, chat, dashboard, documents, event, history, teams
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
    lifespan=lifespan
)

# Attach Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_exception_handler(Exception, global_exception_handler)

# Include API Routers under settings.API_PREFIX
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(event.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(teams.router, prefix=settings.API_PREFIX)
app.include_router(history.router, prefix=settings.API_PREFIX)
app.include_router(documents.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(chat.router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Health"], summary="Root Status Endpoint")
async def root() -> Dict[str, str]:
    """Root status endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online"
    }


@app.get("/health", tags=["Health"], summary="Health Check Endpoint")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Health check endpoint verifying Backend, Database, and Configuration status."""
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
        "version": settings.VERSION
    }
