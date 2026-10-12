from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    # Entering the client runs the lifespan, so this also proves config/*.yaml loads.
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
