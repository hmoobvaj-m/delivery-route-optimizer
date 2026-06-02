import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from delivery_route_api.config import get_settings
from delivery_route_api.logging import configure_logging
from delivery_route_api.readiness import run_readiness_checks

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

@app.get("/ready", tags=["system"])
async def readiness_check() -> JSONResponse:
    result = await run_readiness_checks(settings)

    status_code = 200 if result["ready"] else 503
    status = "ready" if result["ready"] else "not_ready"

    payload: dict[str, Any] = {
        "status": status,
        "service": "api",
        "env": settings.app_env,
        "checks": result["checks"],
    }

    if result["errors"]:
        payload["errors"] = result["errors"]

    return JSONResponse(status_code=status_code, content=payload)

@app.get("/health", tags=["system"])
def health_check() ->  dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "env": settings.app_env,
    }