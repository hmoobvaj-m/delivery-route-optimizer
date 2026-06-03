from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from delivery_route_api.models.route import Route
from delivery_route_api.models.stop import Stop
from delivery_route_api.repositories.routes import RouteRepository
from delivery_route_api.repositories.stops import StopRepository


class InvalidRouteInputError(ValueError):
    pass


class RouteNotFoundError(LookupError):
    pass


@dataclass(frozen=True, slots=True)
class CreateRouteInput:
    name: str
    source: str = "manual"
    driver_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreateStopInput:
    route_id: UUID
    sequence_number: int
    latitude: Decimal
    longitude: Decimal
    external_order_id: str | None = None
    address: str | None = None
    service_time_seconds: int = 120
    priority: int = 0
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    notes: str | None = None


class RouteRepositoryProtocol(Protocol):
    async def create(
        self,
        *,
        name: str,
        source: str = "manual",
        driver_id: str | None = None,
    ) -> Route: ...

    async def get(self, route_id: UUID) -> Route | None: ...

    async def update_stop_count(self, *, route_id: UUID, stop_count: int) -> Route | None: ...


class StopRepositoryProtocol(Protocol):
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
    ) -> Stop: ...

    async def count_for_route(self, route_id: UUID) -> int: ...


class RouteService:
    def __init__(
        self,
        *,
        route_repository: RouteRepositoryProtocol,
        stop_repository: StopRepositoryProtocol,
    ) -> None:
        self.route_repository = route_repository
        self.stop_repository = stop_repository

    @classmethod
    def from_session(cls, session: AsyncSession) -> RouteService:
        return cls(
            route_repository=RouteRepository(session),
            stop_repository=StopRepository(session),
        )

    async def create_route(self, data: CreateRouteInput) -> Route:
        name = data.name.strip()

        if not name:
            raise InvalidRouteInputError("Route name cannot be blank.")

        return await self.route_repository.create(
            name=name,
            source=data.source,
            driver_id=data.driver_id,
        )

    async def add_stop(self, data: CreateStopInput) -> Stop:
        self._validate_stop_input(data)

        route = await self.route_repository.get(data.route_id)

        if route is None:
            raise RouteNotFoundError(f"Route {data.route_id} was not found.")

        stop = await self.stop_repository.create(
            route_id=data.route_id,
            sequence_number=data.sequence_number,
            latitude=data.latitude,
            longitude=data.longitude,
            external_order_id=data.external_order_id,
            address=data.address,
            service_time_seconds=data.service_time_seconds,
            priority=data.priority,
            time_window_start=data.time_window_start,
            time_window_end=data.time_window_end,
            notes=data.notes,
        )

        stop_count = await self.stop_repository.count_for_route(data.route_id)
        await self.route_repository.update_stop_count(
            route_id=data.route_id,
            stop_count=stop_count,
        )

        return stop

    def _validate_stop_input(self, data: CreateStopInput) -> None:
        if data.sequence_number < 1:
            raise InvalidRouteInputError("Stop sequence number must be at least 1.")

        if not Decimal("-90") <= data.latitude <= Decimal("90"):
            raise InvalidRouteInputError("Latitude must be between -90 and 90.")

        if not Decimal("-180") <= data.longitude <= Decimal("180"):
            raise InvalidRouteInputError("Longitude must be between -180 and 180.")

        if data.service_time_seconds < 0:
            raise InvalidRouteInputError("Service time cannot be negative.")

        if data.priority < 0:
            raise InvalidRouteInputError("Priority cannot be negative.")

        if (
            data.time_window_start is not None
            and data.time_window_end is not None
            and data.time_window_start >= data.time_window_end
        ):
            raise InvalidRouteInputError("Time window start must be before time window end.")
