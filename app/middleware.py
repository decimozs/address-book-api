"""HTTP middleware."""
import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger("app.access")


async def log_requests(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Log method, path, status and duration of every request.

    A request id (taken from the incoming X-Request-ID header or generated) is
    included in the log line and echoed back so a call can be traced end to end.
    """
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("[%s] %s %s failed", request_id, request.method, request.url.path)
        raise
    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "[%s] %s %s -> %d (%.1f ms)",
        request_id, request.method, request.url.path, response.status_code, duration_ms,
    )
    return response
