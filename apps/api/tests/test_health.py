from fastapi.testclient import TestClient
from delivery_route_api.main import app

def test_health_check() -> None:
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"    
    assert response.json()["service"] == "api"