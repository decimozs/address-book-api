"""Exception handlers that turn unexpected failures into clean JSON responses."""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Log the real cause server-side; never leak DB internals to the client."""
    logger.error(
        "Database error on %s %s", request.method, request.url.path, exc_info=exc
    )
    return JSONResponse(status_code=500, content={"detail": "Internal database error"})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(SQLAlchemyError, database_error_handler)  # type: ignore[arg-type]
