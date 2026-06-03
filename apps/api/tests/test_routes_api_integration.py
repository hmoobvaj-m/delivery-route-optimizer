from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient


def test_create_route_persists_to_database(integration_client: TestClient):
    create_response = integration_client.post(
        "/routes",
        json={
            "name": "Integration route",
            "source": "manual",
            "driver_id": None,
        },
    )

    assert create_response.status_code == 201

    route = create_response.json()
    route_id = route["id"]

    assert UUID(route_id)
    assert route["name"] == "Integration route"
    assert route["source"] == "manual"
    assert route["driver_id"] is None
    assert route["stop_count"] == 0

    get_response = integration_client.get(f"/routes/{route_id}")

    assert get_response.status_code == 200
    assert get_response.json()["id"] == route_id
    assert get_response.json()["name"] == "Integration route"


def test_add_stop_persists_to_database(integration_client: TestClient):
    create_route_response = integration_client.post(
        "/routes",
        json={
            "name": "Route with persisted stop",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_route_response.status_code == 201

    route_id = create_route_response.json()["id"]

    add_stop_response = integration_client.post(
        f"/routes/{route_id}/stops",
        json={
            "sequence_number": 1,
            "latitude": "43.038900",
            "longitude": "-87.906500",
            "external_order_id": "ORDER-001",
            "address": "123 Main St, Milwaukee, WI",
            "service_time_seconds": 120,
            "priority": 0,
            "time_window_start": None,
            "time_window_end": None,
            "notes": "Integration test stop",
        },
    )

    assert add_stop_response.status_code == 201

    stop = add_stop_response.json()

    assert UUID(stop["id"])
    assert stop["route_id"] == route_id
    assert stop["sequence_number"] == 1
    assert stop["latitude"] == 43.0389
    assert stop["longitude"] == -87.9065
    assert stop["external_order_id"] == "ORDER-001"
    assert stop["address"] == "123 Main St, Milwaukee, WI"

    list_response = integration_client.get(f"/routes/{route_id}/stops")

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == stop["id"]


def test_list_stops_returns_database_stops_in_sequence_order(
    integration_client: TestClient,
):
    create_route_response = integration_client.post(
        "/routes",
        json={
            "name": "Ordered stop route",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_route_response.status_code == 201

    route_id = create_route_response.json()["id"]

    second_stop_response = integration_client.post(
        f"/routes/{route_id}/stops",
        json={
            "sequence_number": 2,
            "latitude": "43.040000",
            "longitude": "-87.910000",
            "address": "Second stop",
        },
    )
    assert second_stop_response.status_code == 201

    first_stop_response = integration_client.post(
        f"/routes/{route_id}/stops",
        json={
            "sequence_number": 1,
            "latitude": "43.030000",
            "longitude": "-87.900000",
            "address": "First stop",
        },
    )
    assert first_stop_response.status_code == 201

    list_response = integration_client.get(f"/routes/{route_id}/stops")

    assert list_response.status_code == 200

    stops = list_response.json()

    assert [stop["sequence_number"] for stop in stops] == [1, 2]
    assert [stop["address"] for stop in stops] == ["First stop", "Second stop"]


def test_add_stop_updates_route_stop_count(integration_client: TestClient):
    create_route_response = integration_client.post(
        "/routes",
        json={
            "name": "Stop count route",
            "source": "manual",
            "driver_id": None,
        },
    )
    assert create_route_response.status_code == 201

    route_id = create_route_response.json()["id"]

    for sequence_number in [1, 2]:
        add_stop_response = integration_client.post(
            f"/routes/{route_id}/stops",
            json={
                "sequence_number": sequence_number,
                "latitude": "43.038900",
                "longitude": "-87.906500",
                "address": f"Stop {sequence_number}",
            },
        )
        assert add_stop_response.status_code == 201

    get_response = integration_client.get(f"/routes/{route_id}")

    assert get_response.status_code == 200
    assert get_response.json()["stop_count"] == 2


def test_missing_route_returns_404_with_real_service(integration_client: TestClient):
    response = integration_client.get(
        "/routes/00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Route not found."