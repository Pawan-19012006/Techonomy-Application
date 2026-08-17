import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.utils.logging import logger
from app.utils.observability import (
    generate_request_id,
    log_structured_event,
    set_request_id,
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware logging HTTP request details, correlation ID, and total duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        t_start = time.perf_counter()

        # 1. End-to-End Request Correlation ID
        incoming_req_id = request.headers.get("X-Request-ID") or request.headers.get("x-request-id")
        request_id = incoming_req_id.strip() if incoming_req_id and incoming_req_id.strip() else generate_request_id()

        set_request_id(request_id)
        request.state.request_id = request_id

        client_host = request.client.host if request.client else "unknown"

        log_structured_event(
            "HTTP_REQUEST_START",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=client_host,
        )

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - t_start) * 1000.0

            log_structured_event(
                "HTTP_REQUEST_COMPLETE",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(process_time_ms, 2),
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
            return response
        except Exception as e:
            process_time_ms = (time.perf_counter() - t_start) * 1000.0
            log_structured_event(
                "HTTP_REQUEST_FAILED",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(process_time_ms, 2),
                error_type=type(e).__name__,
            )
            raise e
