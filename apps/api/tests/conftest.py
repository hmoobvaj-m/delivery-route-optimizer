from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from delivery_route_api.database import get_database_session
from delivery_route_api.main import app
from delivery_route_api.models import Base

TEST_DATABASE_URL_ENV = "TEST_DATABASE_URL"


@pytest.fixture(scope="session")
def test_database_url() -> str:
    database_url = os.getenv(TEST_DATABASE_URL_ENV)

    if database_url is None:
        pytest.skip(f"{TEST_DATABASE_URL_ENV} is required for DB-backed integration tests.")

    return database_url


@pytest.fixture(scope="session")
def test_engine(test_database_url: str) -> Iterator[AsyncEngine]:
    engine = create_async_engine(
        test_database_url,
        poolclass=NullPool,
        echo=False,
    )

    async def setup_database() -> None:
        async with engine.begin() as connection:
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)

    async def teardown_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    asyncio.run(setup_database())

    yield engine

    asyncio.run(teardown_database())


@pytest.fixture
def integration_client(test_engine: AsyncEngine) -> Iterator[TestClient]:
    sessionmaker = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
    )

    async def reset_database() -> None:
        table_names = ", ".join(
            f'"{table.name}"'
            for table in Base.metadata.sorted_tables
        )

        if not table_names:
            return

        async with test_engine.begin() as connection:
            await connection.execute(
                text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"),
            )

    async def override_get_database_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    asyncio.run(reset_database())

    app.dependency_overrides[get_database_session] = override_get_database_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_database_session, None)