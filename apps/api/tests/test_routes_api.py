from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from delivery_route_api.api.routes import get_route_service
from delivery_route_api.main import app
from delivery_route_api.services.routes import (
    CreateRouteInput,
    CreateStopInput,
    RouteNotFoundError,
)


@dataclass(slots=True)
class FakeRoute:
    id: UUID
    name: str
    source: str
    driver_id: str | None
    stop_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class FakeStop:
    id: UUID
    route_id: UUID
    sequence_number: int
    latitude: Decimal
    longitude: Decimal
    external_order_id: str | None
    address: str | None
    service_time_seconds: int
    priority: int
    time_window_start: datetime | None
    time_window_end: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class FakeRouteService:
    def __init__(self) -> None:
        self.routes: dict[UUID, FakeRoute] = {}
        self.stops: dict[UUID, list[FakeStop]] = {}

    async def create_route(self, data: CreateRouteInput) -> FakeRoute:
        now = datetime.now(UTC)
        route = FakeRoute(
            id=uuid4(),
            name=data.name,
            source=data.source,
            driver_id=data.driver_id,
            stop_count=0,
            created_at=now,
            updated_at=now,
        )
        self.routes[route.id] = route
        self.stops[route.id] = []
        return route

    async def get_route(self, route_id: UUID) -> FakeRoute | None:
        return self.routes.get(route_id)

    async def add_stop(self, data: CreateStopInput) -> FakeStop:
        if data.route_id not in self.routes:
            raise RouteNotFoundError(f"Route {data.route_id} was not found.")

        now = datetime.now(UTC)
        stop = FakeStop(
            id=uuid4(),
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
            created_at=now,
            updated_at=now,
        )

        self.stops[data.route_id].append(stop)
        self.routes[data.route_id].stop_count = len(self.stops[data.route_id])
        self.routes[data.route_id].updated_at = now

        return stop

    async def list_stops(self, route_id: UUID) -> list[FakeStop]:
        if route_id not in self.routes:
            raise RouteNotFoundError(f"Route {route_id} was not found.")

        return sorted(
            self.stops[route_id],
            key=lambda stop: stop.sequence_number,
        )


@pytest.fixture
def fake_route_service() -> FakeRouteService:
    return FakeRouteService()


@pytest.fixture
def client(fake_route_service: FakeRouteService):
    app.dependency_overrides[get_route_service] = lambda: fake_route_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_route(client: TestClient):
    response = client.post(
        "/routes",
        json={
            "name": "Morning delivery route",
            "source": "manual",
            "driver_id": None,
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert UUID(data["id"])
    assert data["name"] == "Morning delivery route"
    assert data["source"] == "manual"
    assert data["driver_id"] is None
    assert data["stop_count"] == 0


def test_get_route(client: TestClient):
    create_response = client.post(
        "/routes",
        json={
            "name": "Afternoon delivery route",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_response.status_code == 201

    route_id = create_response.json()["id"]

    response = client.get(f"/routes/{route_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == route_id
    assert data["name"] == "Afternoon delivery route"
    assert data["source"] == "manual"


def test_get_missing_route_returns_404(client: TestClient):
    response = client.get(
        "/routes/00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found."


def test_add_stop(client: TestClient):
    create_route_response = client.post(
        "/routes",
        json={
            "name": "Route with stops",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_route_response.status_code == 201

    route_id = create_route_response.json()["id"]

    response = client.post(
        f"/routes/{route_id}/stops",
        json={
            "sequence_number": 1,
            "latitude": "43.0389",
            "longitude": "-87.9065",
            "external_order_id": "ORDER-001",
            "address": "123 Main St, Milwaukee, WI",
            "service_time_seconds": 120,
            "priority": 0,
            "time_window_start": None,
            "time_window_end": None,
            "notes": "Front door delivery",
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert UUID(data["id"])
    assert data["route_id"] == route_id
    assert data["sequence_number"] == 1
    assert data["latitude"] == 43.0389
    assert data["longitude"] == -87.9065
    assert data["external_order_id"] == "ORDER-001"
    assert data["address"] == "123 Main St, Milwaukee, WI"
    assert data["service_time_seconds"] == 120
    assert data["priority"] == 0
    assert data["notes"] == "Front door delivery"


def test_list_stops(client: TestClient):
    create_route_response = client.post(
        "/routes",
        json={
            "name": "Route stop list",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_route_response.status_code == 201

    route_id = create_route_response.json()["id"]

    add_stop_response = client.post(
        f"/routes/{route_id}/stops",
        json={
            "sequence_number": 1,
            "latitude": "43.0389",
            "longitude": "-87.9065",
            "external_order_id": "ORDER-001",
            "address": "123 Main St, Milwaukee, WI",
            "service_time_seconds": 120,
            "priority": 0,
            "time_window_start": None,
            "time_window_end": None,
            "notes": None,
        },
    )
    assert add_stop_response.status_code == 201

    response = client.get(f"/routes/{route_id}/stops")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["route_id"] == route_id
    assert data[0]["sequence_number"] == 1
    assert data[0]["address"] == "123 Main St, Milwaukee, WI"


def test_add_stop_to_missing_route_returns_404(client: TestClient):
    response = client.post(
        "/routes/00000000-0000-0000-0000-000000000000/stops",
        json={
            "sequence_number": 1,
            "latitude": "43.0389",
            "longitude": "-87.9065",
            "external_order_id": None,
            "address": "123 Main St, Milwaukee, WI",
            "service_time_seconds": 120,
            "priority": 0,
            "time_window_start": None,
            "time_window_end": None,
            "notes": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found."


def test_list_stops_for_missing_route_returns_404(client: TestClient):
    response = client.get(
        "/routes/00000000-0000-0000-0000-000000000000/stops",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found."


def test_add_stop_with_invalid_sequence_number_returns_422(client: TestClient):
    create_route_response = client.post(
        "/routes",
        json={
            "name": "Invalid stop route",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_route_response.status_code == 201

    route_id = create_route_response.json()["id"]

    response = client.post(
        f"/routes/{route_id}/stops",
        json={
            "sequence_number": 0,
            "latitude": "43.0389",
            "longitude": "-87.9065",
            "address": "123 Main St, Milwaukee, WI",
        },
    )

    assert response.status_code == 422
