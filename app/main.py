"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import Base, engine
from app.logging_config import setup_logging
from app.routers import addresses

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database ready at %s", settings.database_url)
    yield


app = FastAPI(
    title=settings.app_name,
    description="Create, update, delete and search addresses by distance.",
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(addresses.router)
