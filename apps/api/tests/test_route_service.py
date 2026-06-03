from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from delivery_route_api.services.routes import (
    CreateRouteInput,
    CreateStopInput,
    InvalidRouteInputError,
    RouteNotFoundError,
    RouteService,
)


class FakeRouteRepository:
    def __init__(self) -> None:
        self.routes: dict[UUID, SimpleNamespace] = {}
        self.updated_stop_counts: list[tuple[UUID, int]] = []

    async def create(
        self,
        *,
        name: str,
        source: str = "manual",
        driver_id: str | None = None,
    ) -> SimpleNamespace:
        route = SimpleNamespace(
            id=uuid4(),
            name=name,
            source=source,
            driver_id=driver_id,
            original_stop_count=0,
        )
        self.routes[route.id] = route
        return route

    async def get(self, route_id: UUID) -> SimpleNamespace | None:
        return self.routes.get(route_id)

    async def update_stop_count(
        self,
        *,
        route_id: UUID,
        stop_count: int,
    ) -> SimpleNamespace | None:
        route = self.routes.get(route_id)

        if route is None:
            return None

        route.original_stop_count = stop_count
        self.updated_stop_counts.append((route_id, stop_count))

        return route


class FakeStopRepository:
    def __init__(self) -> None:
        self.stops: list[SimpleNamespace] = []

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
        **_: object,
    ) -> SimpleNamespace:
        stop = SimpleNamespace(
            id=uuid4(),
            route_id=route_id,
            sequence_number=sequence_number,
            latitude=latitude,
            longitude=longitude,
            external_order_id=external_order_id,
            address=address,
            service_time_seconds=service_time_seconds,
            priority=priority,
        )
        self.stops.append(stop)
        return stop

    async def count_for_route(self, route_id: UUID) -> int:
        return sum(1 for stop in self.stops if stop.route_id == route_id)


@pytest.fixture
def route_repository() -> FakeRouteRepository:
    return FakeRouteRepository()


@pytest.fixture
def stop_repository() -> FakeStopRepository:
    return FakeStopRepository()


@pytest.fixture
def route_service(
    route_repository: FakeRouteRepository,
    stop_repository: FakeStopRepository,
) -> RouteService:
    return RouteService(
        route_repository=route_repository,
        stop_repository=stop_repository,
    )


@pytest.mark.anyio
async def test_create_route_success(route_service: RouteService) -> None:
    route = await route_service.create_route(
        CreateRouteInput(
            name=" Morning Route ",
            source="manual",
            driver_id="driver-1",
        )
    )

    assert route.name == "Morning Route"
    assert route.source == "manual"
    assert route.driver_id == "driver-1"


@pytest.mark.anyio
async def test_create_route_rejects_blank_name(route_service: RouteService) -> None:
    with pytest.raises(InvalidRouteInputError):
        await route_service.create_route(CreateRouteInput(name="   "))


@pytest.mark.anyio
async def test_add_stop_success(
    route_service: RouteService,
    route_repository: FakeRouteRepository,
) -> None:
    route = await route_service.create_route(CreateRouteInput(name="Route A"))

    stop = await route_service.add_stop(
        CreateStopInput(
            route_id=route.id,
            sequence_number=1,
            latitude=Decimal("43.0389"),
            longitude=Decimal("-87.9065"),
            address="Milwaukee, WI",
        )
    )

    assert stop.route_id == route.id
    assert stop.sequence_number == 1
    assert stop.address == "Milwaukee, WI"
    assert route_repository.updated_stop_counts == [(route.id, 1)]


@pytest.mark.anyio
async def test_add_stop_rejects_missing_route(route_service: RouteService) -> None:
    with pytest.raises(RouteNotFoundError):
        await route_service.add_stop(
            CreateStopInput(
                route_id=uuid4(),
                sequence_number=1,
                latitude=Decimal("43.0389"),
                longitude=Decimal("-87.9065"),
            )
        )


@pytest.mark.anyio
async def test_add_stop_rejects_invalid_coordinates(route_service: RouteService) -> None:
    route_id = uuid4()

    with pytest.raises(InvalidRouteInputError):
        await route_service.add_stop(
            CreateStopInput(
                route_id=route_id,
                sequence_number=1,
                latitude=Decimal("91"),
                longitude=Decimal("-87.9065"),
            )
        )
