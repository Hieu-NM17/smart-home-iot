import math

from app.database.database import SessionLocal
from app.services.device_service import (
    get_device_by_device_id,
    update_device_online_status,
    update_device_state,
)
from app.services.sensor_service import (
    get_sensor_by_sensor_id,
    save_reading,
)

TOPIC_PREFIX = "home"


def handle_message(topic: str, payload, session_factory=SessionLocal) -> None:
    """Route an incoming MQTT message: home/{room}/{device_id}/{kind}."""
    parts = topic.split("/")

    if len(parts) != 4 or parts[0] != TOPIC_PREFIX:
        return

    _, _room, device_id, kind = parts

    if kind == "state":
        handle_state(device_id, payload, session_factory)
    elif kind == "sensor":
        # The sensor is identified by payload["sensor_id"]; the device
        # segment of the topic is not used for lookup.
        handle_sensor(payload, session_factory)
    elif kind == "status":
        # One board hosts several devices: the payload lists their device_ids.
        handle_status(payload, session_factory)


def handle_state(device_id: str, payload, session_factory=SessionLocal) -> None:
    if not isinstance(payload, str):
        print(f"MQTT state ignored ({device_id}): unexpected payload {payload!r}")
        return

    # paho calls us from its own thread, so open a dedicated DB session.
    with session_factory() as db:
        device = get_device_by_device_id(db, device_id)

        if device is None:
            print(f"MQTT state ignored: unknown device {device_id}")
            return

        try:
            update_device_state(db, device.id, payload)
        except ValueError:
            print(f"MQTT state ignored ({device_id}): invalid state {payload!r}")
            return

        print(f"Device {device_id} state -> {payload}")


def handle_sensor(payload, session_factory=SessionLocal) -> None:
    if not isinstance(payload, dict):
        print(f"MQTT sensor ignored: unexpected payload {payload!r}")
        return

    sensor_id = payload.get("sensor_id")
    value = payload.get("value")

    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)

    if not isinstance(sensor_id, str) or not is_number or not math.isfinite(value):
        print(f"MQTT sensor ignored: invalid payload {payload!r}")
        return

    with session_factory() as db:
        sensor = get_sensor_by_sensor_id(db, sensor_id)

        if sensor is None:
            print(f"MQTT sensor ignored: unknown sensor {sensor_id}")
            return

        save_reading(db, sensor.id, float(value))

        print(f"Sensor {sensor_id} reading -> {value}")


def handle_status(payload, session_factory=SessionLocal) -> None:
    if not isinstance(payload, dict):
        print(f"MQTT status ignored: unexpected payload {payload!r}")
        return

    status = payload.get("status")
    device_ids = payload.get("devices")

    if status not in ("online", "offline") or not isinstance(device_ids, list):
        print(f"MQTT status ignored: invalid payload {payload!r}")
        return

    is_online = status == "online"

    with session_factory() as db:
        for device_id in device_ids:
            if not isinstance(device_id, str):
                continue

            device = get_device_by_device_id(db, device_id)

            if device is None:
                print(f"MQTT status ignored: unknown device {device_id}")
                continue

            update_device_online_status(db, device.id, is_online)
            print(f"Device {device_id} is_online -> {is_online}")
