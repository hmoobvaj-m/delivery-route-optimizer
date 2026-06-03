from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_route_api.models.stop import Stop


class StopRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        route_id: UUID,
        sequence_number: int,
        latitude: Decimal,
        longitude: Decimal,
        external_order_id: str | None = None,
        address: str | None = None,
        service_time_seconds: int = 120,
        priority: int = 0,
        time_window_start: datetime | None = None,
        time_window_end: datetime | None = None,
        notes: str | None = None,
    ) -> Stop:
        stop = Stop(
            route_id=route_id,
            external_order_id=external_order_id,
            sequence_number=sequence_number,
            address=address,
            latitude=latitude,
            longitude=longitude,
            location=WKTElement(f"POINT({longitude} {latitude})", srid=4326),
            service_time_seconds=service_time_seconds,
            priority=priority,
            time_window_start=time_window_start,
            time_window_end=time_window_end,
            notes=notes,
        )

        self.session.add(stop)
        await self.session.flush()
        await self.session.refresh(stop)

        return stop

    async def list_for_route(self, route_id: UUID) -> list[Stop]:
        statement = (
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence_number.asc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def count_for_route(self, route_id: UUID) -> int:
        statement = select(func.count()).select_from(Stop).where(Stop.route_id == route_id)
        result = await self.session.execute(statement)
        return int(result.scalar_one())
