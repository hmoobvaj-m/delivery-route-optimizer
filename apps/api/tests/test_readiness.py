from typing import Any

from fastapi.testclient import TestClient

from delivery_route_api.main import app


def test_ready_success(monkeypatch: Any) -> None:
    async def fake_readiness_checks(_: Any) -> dict[str, Any]:
        return {
            "ready": True,
            "checks": {
                "postgres": "ok",
                "redis": "ok",
            },
            "errors": {}
        }
        
    monkeypatch.setattr("delivery_route_api.main.run_readiness_checks", fake_readiness_checks)
    
    client = TestClient(app)
    response = client.get("/ready")
    
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "api",
        "env": "dev",
        "checks": {
            "postgres": "ok",
            "redis": "ok",
        },
    }

def test_ready_depedency_failure(monkeypatch: Any) -> None:
    async def fake_readiness_checks(_: Any) -> dict[str, Any]:
        return {
            "ready": False,
            "checks": {
                "postgres": "ok",
                "redis": "error"
            },
            "errors": {
                "redis": "connection refused",
            },
        }
    
    monkeypatch.setattr("delivery_route_api.main.run_readiness_checks", fake_readiness_checks)
    
    client = TestClient(app)
    response = client.get("/ready")
    
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["postgres"] == "ok"
    assert response.json()["checks"]["redis"] == "error"
    assert response.json()["errors"]["redis"] == "connection refused"