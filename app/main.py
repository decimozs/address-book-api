"""FastAPI application entry point."""
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.errors import register_exception_handlers
from app.logging_config import setup_logging
from app.middleware import log_requests
from app.routers import addresses, health

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready at %s", settings.database_url)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Create, update, delete and search addresses by distance.",
    version="1.0.0",
    lifespan=lifespan,
)
register_exception_handlers(app)
app.middleware("http")(log_requests)
app.include_router(health.router)
app.include_router(addresses.router)
