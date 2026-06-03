from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_route_api.models.route import Route


class RouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        name: str,
        source: str = "manual",
        driver_id: str | None = None,
    ) -> Route:
        route = Route(
            name=name,
            source=source,
            driver_id=driver_id,
        )

        self.session.add(route)
        await self.session.flush()
        await self.session.refresh(route)

        return route

    async def get(self, route_id: UUID) -> Route | None:
        return await self.sesion.get(Route, route_id)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Route]:
        statement = select(Route).order_by(Route.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def update_stop_count(self, *, route_id: UUID, stop_count: int) -> Route | None:
        route = await self.get(route_id)
        if route is None:
            return None

        route.original_stop_count = stop_count

        await self.session.flush()
        await self.session.refresh(route)
        return route
