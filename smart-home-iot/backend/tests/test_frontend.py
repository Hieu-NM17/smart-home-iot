from fastapi.testclient import TestClient

from app.main import app


def test_frontend_is_served_at_root():
    # No "with": we do not want startup (broker + real DB) here.
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Smart Home" in response.text


def test_api_routes_are_not_shadowed_by_frontend():
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/devices" in response.json()["paths"]
