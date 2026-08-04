import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.utils.logging import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware logging HTTP request details and duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        formatted_process_time = f"{process_time:.2f}ms"

        logger.info(
            f"HTTP {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Client: {client_host} "
            f"Duration: {formatted_process_time}"
        )

        response.headers["X-Process-Time"] = formatted_process_time
        return response
