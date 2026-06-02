import asyncio

from delivery_route_api.config import Settings
from delivery_route_api.database import create_database_engine


def test_create_database_engine_uses_configured_database_url() -> None:
    settings = Settings(database_url="postgresql+asyncpg://app:app@localhost:5433/delivery_routes")

    engine = create_database_engine(settings)

    try:
        assert engine.url.drivername == "postgresql+asyncpg"
        assert engine.url.username == "app"
        assert engine.url.host == "localhost"
        assert engine.url.port == 5433
        assert engine.url.database == "delivery_routes"
    finally:
        asyncio.run(engine.dispose())
