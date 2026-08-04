from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.utils.logging import logger


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global catch-all exception handler converting uncaught exceptions to JSON response.

    Args:
        request: Incoming HTTP Request.
        exc: Exception instance.

    Returns:
        JSONResponse: 500 Internal Server Error payload.
    """
    logger.error(
        f"Unhandled exception during {request.method} {request.url.path}: {exc}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "path": request.url.path
        }
    )
