from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.seed import seed_db
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.mqtt.handlers import handle_message

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


def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with TestingSessionLocal() as db:
        seed_db(db)


def light_state():
    with TestingSessionLocal() as db:
        return db.query(Device).filter(
            Device.device_id == "light_01"
        ).one().state


def send(topic, payload):
    handle_message(topic, payload, session_factory=TestingSessionLocal)


def test_state_message_updates_device():
    fresh_db()

    assert light_state() == "off"

    send("home/living_room/light_01/state", "on")
    assert light_state() == "on"

    send("home/living_room/light_01/state", "off")
    assert light_state() == "off"


def test_invalid_state_is_ignored():
    fresh_db()

    send("home/living_room/light_01/state", "on")
    send("home/living_room/light_01/state", "banana")

    assert light_state() == "on"


def test_non_string_payload_is_ignored():
    fresh_db()

    send("home/living_room/light_01/state", {"state": "on"})
    send("home/living_room/light_01/state", 1)

    assert light_state() == "off"


def test_unknown_device_is_ignored():
    fresh_db()

    send("home/living_room/ghost_99/state", "on")

    assert light_state() == "off"


def test_other_topics_are_ignored():
    fresh_db()

    send("home/living_room/light_01/command", "on")
    send("home/living_room/light_01", "on")
    send("other/living_room/light_01/state", "on")

    assert light_state() == "off"


def readings():
    with TestingSessionLocal() as db:
        return [r.value for r in db.query(SensorReading).order_by(SensorReading.id)]


def sensor_payload(**overrides):
    payload = {
        "sensor_id": "temperature_01",
        "sensor_type": "temperature",
        "value": 25.0,
        "unit": "celsius",
    }
    payload.update(overrides)
    return payload


def test_sensor_message_saves_reading():
    fresh_db()

    send("home/living_room/temperature_01/sensor", sensor_payload(value=25.5))
    send("home/living_room/temperature_01/sensor", sensor_payload(value=26))

    assert readings() == [25.5, 26.0]


def test_sensor_is_found_by_payload_not_topic():
    fresh_db()

    # topic device segment is "dht22_01" but the payload names the sensor
    send("home/living_room/dht22_01/sensor", sensor_payload(value=21.0))

    assert readings() == [21.0]


def test_invalid_sensor_messages_are_ignored():
    fresh_db()

    topic = "home/living_room/temperature_01/sensor"

    send(topic, "not json")
    send(topic, sensor_payload(sensor_id="ghost_99"))
    send(topic, sensor_payload(sensor_id=None))
    send(topic, sensor_payload(value="hot"))
    send(topic, sensor_payload(value=True))
    send(topic, sensor_payload(value=float("nan")))
    send(topic, {"sensor_id": "temperature_01"})

    assert readings() == []


def online_flags():
    with TestingSessionLocal() as db:
        return {d.device_id: d.is_online for d in db.query(Device).all()}


STATUS_TOPIC = "home/living_room/esp32_smart_home/status"


def test_status_online_then_offline_updates_listed_devices():
    fresh_db()

    assert online_flags() == {"light_01": False, "dht22_01": False}

    send(STATUS_TOPIC, {"status": "online", "devices": ["light_01", "dht22_01"]})
    assert online_flags() == {"light_01": True, "dht22_01": True}

    send(STATUS_TOPIC, {"status": "offline", "devices": ["light_01", "dht22_01"]})
    assert online_flags() == {"light_01": False, "dht22_01": False}


def test_status_only_touches_listed_devices():
    fresh_db()

    send(STATUS_TOPIC, {"status": "online", "devices": ["light_01"]})

    assert online_flags() == {"light_01": True, "dht22_01": False}


def test_invalid_status_messages_are_ignored():
    fresh_db()

    send(STATUS_TOPIC, "online")
    send(STATUS_TOPIC, {"status": "maybe", "devices": ["light_01"]})
    send(STATUS_TOPIC, {"status": "online", "devices": "light_01"})
    send(STATUS_TOPIC, {"status": "online"})

    assert online_flags() == {"light_01": False, "dht22_01": False}


def test_status_skips_unknown_and_non_string_devices():
    fresh_db()

    send(STATUS_TOPIC, {"status": "online", "devices": [None, 5, "ghost_99", "light_01"]})

    assert online_flags() == {"light_01": True, "dht22_01": False}


def test_humidity_reading_is_saved():
    fresh_db()

    send(
        "home/living_room/humidity_01/sensor",
        sensor_payload(sensor_id="humidity_01", sensor_type="humidity", value=61.5, unit="percent"),
    )

    assert readings() == [61.5]
