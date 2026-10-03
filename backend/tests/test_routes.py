from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.routes.devices import router as device_router
from app.api.routes.rooms import router as room_router
from app.api.routes.sensors import router as sensor_router
from app.database.database import Base, get_db
from app.mqtt.deps import get_publisher


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app = FastAPI()

app.include_router(room_router, prefix="/api")
app.include_router(device_router, prefix="/api")
app.include_router(sensor_router, prefix="/api")

app.dependency_overrides[get_db] = override_get_db


class FakePublisher:
    def __init__(self):
        self.messages = []

    def is_connected(self):
        return True

    def publish(self, topic, payload):
        self.messages.append((topic, payload))

client = TestClient(app)


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_database():
    Base.metadata.drop_all(bind=engine)


def test_get_rooms():
    setup_database()

    response = client.get("/api/rooms")

    assert response.status_code == 200
    assert response.json() == []

    teardown_database()


def test_create_room():
    setup_database()

    response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
            "description": "Main room",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Living Room"
    assert data["description"] == "Main room"
    assert "id" in data
    assert "created_at" in data

    teardown_database()


def test_get_room():
    setup_database()

    response = client.post(
        "/api/rooms",
        json={
            "name": "Bedroom",
            "description": "Bedroom room",
        },
    )

    room_id = response.json()["id"]

    response = client.get(f"/api/rooms/{room_id}")

    assert response.status_code == 200
    assert response.json()["id"] == room_id
    assert response.json()["name"] == "Bedroom"

    teardown_database()


def test_update_room():
    setup_database()

    response = client.post(
        "/api/rooms",
        json={
            "name": "Bedroom",
            "description": "Old description",
        },
    )

    room_id = response.json()["id"]

    response = client.put(
        f"/api/rooms/{room_id}",
        json={
            "name": "Master Bedroom",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Master Bedroom"
    assert data["description"] == "Updated description"

    teardown_database()


def test_delete_room():
    setup_database()

    response = client.post(
        "/api/rooms",
        json={
            "name": "Kitchen",
            "description": "Kitchen room",
        },
    )

    room_id = response.json()["id"]

    response = client.delete(f"/api/rooms/{room_id}")

    assert response.status_code == 204

    response = client.get(f"/api/rooms/{room_id}")

    assert response.status_code == 404

    teardown_database()


def test_get_devices():
    setup_database()

    response = client.get("/api/devices")

    assert response.status_code == 200
    assert response.json() == []

    teardown_database()


def test_create_device():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
            "description": "Main room",
        },
    )

    room_id = room_response.json()["id"]

    response = client.post(
        "/api/devices",
        json={
            "device_id": "light_01",
            "name": "Living Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["device_id"] == "light_01"
    assert data["name"] == "Living Light"
    assert data["device_type"] == "light"
    assert data["room_id"] == room_id

    teardown_database()


def test_get_device():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "light_01",
            "name": "Living Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    response = client.get(f"/api/devices/{device_id}")

    assert response.status_code == 200
    assert response.json()["id"] == device_id

    teardown_database()


def test_update_device():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "light_01",
            "name": "Living Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    response = client.put(
        f"/api/devices/{device_id}",
        json={
            "name": "Main Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Main Light"

    teardown_database()


def test_delete_device():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "light_01",
            "name": "Living Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    response = client.delete(f"/api/devices/{device_id}")

    assert response.status_code == 204

    response = client.get(f"/api/devices/{device_id}")

    assert response.status_code == 404

    teardown_database()


def create_light(client):
    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "light_01",
            "name": "Living Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    return device_response.json()["id"]


def test_device_command():
    setup_database()

    fake_publisher = FakePublisher()
    app.dependency_overrides[get_publisher] = lambda: fake_publisher

    try:
        device_id = create_light(client)

        response = client.post(
            f"/api/devices/{device_id}/command",
            json={
                "command": "on",
            },
        )
    finally:
        app.dependency_overrides.pop(get_publisher, None)

    assert response.status_code == 200

    data = response.json()

    assert data["topic"] == "home/living_room/light_01/command"
    assert data["payload"]["command"] == "on"

    # Raw string, not JSON: this is what the ESP32 compares against.
    assert fake_publisher.messages == [
        ("home/living_room/light_01/command", "on"),
    ]

    teardown_database()


def test_device_command_broker_not_connected():
    setup_database()

    device_id = create_light(client)

    response = client.post(
        f"/api/devices/{device_id}/command",
        json={
            "command": "on",
        },
    )

    assert response.status_code == 503

    teardown_database()


def test_invalid_device_command():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "light_01",
            "name": "Living Light",
            "device_type": "light",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    response = client.post(
        f"/api/devices/{device_id}/command",
        json={
            "command": "toggle",
        },
    )

    assert response.status_code == 422

    teardown_database()


def test_get_sensors():
    setup_database()

    response = client.get("/api/sensors")

    assert response.status_code == 200
    assert response.json() == []

    teardown_database()


def test_create_sensor():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "temperature_device",
            "name": "Temperature Device",
            "device_type": "sensor",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    response = client.post(
        "/api/sensors",
        json={
            "sensor_id": "temperature_01",
            "name": "Temperature Sensor",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["sensor_id"] == "temperature_01"
    assert data["sensor_type"] == "temperature"
    assert data["device_id"] == device_id
    assert data["unit"] == "celsius"

    teardown_database()


def test_get_sensor():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "temperature_device",
            "name": "Temperature Device",
            "device_type": "sensor",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    sensor_response = client.post(
        "/api/sensors",
        json={
            "sensor_id": "temperature_01",
            "name": "Temperature Sensor",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    )

    sensor_id = sensor_response.json()["id"]

    response = client.get(f"/api/sensors/{sensor_id}")

    assert response.status_code == 200
    assert response.json()["id"] == sensor_id

    teardown_database()


def test_update_sensor():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "temperature_device",
            "name": "Temperature Device",
            "device_type": "sensor",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    sensor_response = client.post(
        "/api/sensors",
        json={
            "sensor_id": "temperature_01",
            "name": "Temperature Sensor",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    )

    sensor_id = sensor_response.json()["id"]

    response = client.put(
        f"/api/sensors/{sensor_id}",
        json={
            "name": "Living Temperature",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Living Temperature"

    teardown_database()


def test_delete_sensor():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "temperature_device",
            "name": "Temperature Device",
            "device_type": "sensor",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    sensor_response = client.post(
        "/api/sensors",
        json={
            "sensor_id": "temperature_01",
            "name": "Temperature Sensor",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    )

    sensor_id = sensor_response.json()["id"]

    response = client.delete(f"/api/sensors/{sensor_id}")

    assert response.status_code == 204

    response = client.get(f"/api/sensors/{sensor_id}")

    assert response.status_code == 404

    teardown_database()


def test_sensor_readings():
    setup_database()

    room_response = client.post(
        "/api/rooms",
        json={
            "name": "Living Room",
        },
    )

    room_id = room_response.json()["id"]

    device_response = client.post(
        "/api/devices",
        json={
            "device_id": "temperature_device",
            "name": "Temperature Device",
            "device_type": "sensor",
            "room_id": room_id,
        },
    )

    device_id = device_response.json()["id"]

    sensor_response = client.post(
        "/api/sensors",
        json={
            "sensor_id": "temperature_01",
            "name": "Temperature Sensor",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    )

    sensor_id = sensor_response.json()["id"]

    response = client.post(
        f"/api/sensors/{sensor_id}/readings",
        json={
            "value": 25.5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sensor_id"] == sensor_id
    assert data["value"] == 25.5

    response = client.get(
        f"/api/sensors/{sensor_id}/readings"
    )

    assert response.status_code == 200

    readings = response.json()

    assert len(readings) == 1
    assert readings[0]["value"] == 25.5

    teardown_database()


def test_sensor_readings_limit():
    setup_database()

    room_id = client.post("/api/rooms", json={"name": "Living Room"}).json()["id"]

    device_id = client.post(
        "/api/devices",
        json={
            "device_id": "temperature_device",
            "name": "Temperature Device",
            "device_type": "sensor",
            "room_id": room_id,
        },
    ).json()["id"]

    sensor_id = client.post(
        "/api/sensors",
        json={
            "sensor_id": "temperature_01",
            "name": "Temperature Sensor",
            "sensor_type": "temperature",
            "device_id": device_id,
            "unit": "celsius",
        },
    ).json()["id"]

    for value in (20.0, 21.0, 22.0):
        client.post(f"/api/sensors/{sensor_id}/readings", json={"value": value})

    response = client.get(f"/api/sensors/{sensor_id}/readings?limit=1")

    assert response.status_code == 200
    assert [r["value"] for r in response.json()] == [22.0]

    assert len(client.get(f"/api/sensors/{sensor_id}/readings").json()) == 3
    assert client.get(f"/api/sensors/{sensor_id}/readings?limit=0").status_code == 422

    teardown_database()
