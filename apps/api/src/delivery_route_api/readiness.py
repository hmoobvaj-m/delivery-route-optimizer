from __future__ import annotations

import asyncio
from typing import TypedDict

import asyncpg
from redis.asyncio import Redis

from delivery_route_api.config import Settings


class ReadinessResult(TypedDict):
    ready: bool
    checks: dict[str, str]
    errors: dict[str, str]


def _to_asyncpg_dsn(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

    return database_url


async def check_postgres(settings: Settings) -> None:
    connection = await asyncpg.connect(
        dsn=_to_asyncpg_dsn(settings.database_url),
        timeout=settings.readiness_timeout_seconds,
    )

    try:
        await connection.execute("SELECT 1")
    finally:
        await connection.close()


async def check_redis(settings: Settings) -> None:
    client = Redis.from_url(
        settings.redis_url,
        socket_connect_timeout=settings.readiness_timeout_seconds,
        socket_timeout=settings.readiness_timeout_seconds,
        decode_responses=True,
    )

    try:
        response = await client.ping()
        if response is not True:
            raise RuntimeError("Redis ping did not return True")
    finally:
        await client.aclose()


async def run_readiness_checks(settings: Settings) -> ReadinessResult:
    checks: dict[str, str] = {}
    errors: dict[str, str] = {}

    dependency_checks = {
        "postgres": check_postgres(settings),
        "redis": check_redis(settings),
    }

    results = await asyncio.gather(
        *dependency_checks.values(),
        return_exceptions=True,
    )

    for dependency_name, result in zip(dependency_checks.keys(), results, strict=True):
        if isinstance(result, Exception):
            checks[dependency_name] = "error"
            errors[dependency_name] = str(result)
        else:
            checks[dependency_name] = "ok"

    return {
        "ready": not errors,
        "checks": checks,
        "errors": errors,
    }
