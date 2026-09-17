from fastapi.testclient import TestClient


def test_health_returns_ok(valid_env):
    from app.main import create_app

    client = TestClient(create_app())
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_returns_service_info(valid_env):
    from app.main import create_app

    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["health"] == "/health"
