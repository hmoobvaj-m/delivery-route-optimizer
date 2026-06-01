import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from delivery_route_api.config import get_settings
from delivery_route_api.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "api_startup",
        extra = {
            "service": "api",
            "env": settings.app_env
        },
    )
    yield
    logger.info(
        "app_shutdown",
        extra = {
            "service": "api",
            "env": settings.app_env
        }
    )

app = FastAPI(
    title = "Delivery Route Optimizer API",
    version = "0.1.0",
    description = "Backend API for route optimnization, routing jobs, and delivery route data",
    lifespan = lifespan,
)

@app.get("/health", tags=["system"])
def health_check() ->  dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "env": settings.app_env,
    }