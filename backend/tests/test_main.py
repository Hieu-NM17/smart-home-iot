from fastapi.testclient import TestClient

from app.main import app, mqtt_client


def test_app_lifecycle(monkeypatch):
    calls = []

    monkeypatch.setattr(
        mqtt_client,
        "connect",
        lambda: calls.append("connect"),
    )

    monkeypatch.setattr(
        mqtt_client,
        "start_loop",
        lambda: calls.append("start_loop"),
    )

    monkeypatch.setattr(
        mqtt_client,
        "stop_loop",
        lambda: calls.append("stop_loop"),
    )

    monkeypatch.setattr(
        mqtt_client,
        "disconnect",
        lambda: calls.append("disconnect"),
    )

    with TestClient(app):
        assert calls == ["connect", "start_loop"]

    assert calls == [
        "connect",
        "start_loop",
        "stop_loop",
        "disconnect",
    ]