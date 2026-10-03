from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.room import Room
from app.models.sensor import Sensor

# Topic command = home/{room.name.lower().replace(" ", "_")}/{device_id}/command
# -> "Living Room" gives home/living_room/light_01/command
ROOM_NAME = "Living Room"
LIGHT_DEVICE_ID = "light_01"
DHT_DEVICE_ID = "dht22_01"
TEMPERATURE_SENSOR_ID = "temperature_01"
HUMIDITY_SENSOR_ID = "humidity_01"


def seed_db(db: Session) -> None:
    """Create the default data used by the ESP32. Safe to call many times."""
    room = db.query(Room).filter(Room.name == ROOM_NAME).first()

    if room is None:
        room = Room(name=ROOM_NAME, description="Main room")
        db.add(room)
        db.flush()

    light = db.query(Device).filter(
        Device.device_id == LIGHT_DEVICE_ID
    ).first()

    if light is None:
        db.add(
            Device(
                device_id=LIGHT_DEVICE_ID,
                name="Living Room Light",
                device_type="light",
                room_id=room.id,
            )
        )

    dht = db.query(Device).filter(
        Device.device_id == DHT_DEVICE_ID
    ).first()

    if dht is None:
        dht = Device(
            device_id=DHT_DEVICE_ID,
            name="Living Room DHT22",
            device_type="sensor",
            room_id=room.id,
        )
        db.add(dht)
        db.flush()

    sensor = db.query(Sensor).filter(
        Sensor.sensor_id == TEMPERATURE_SENSOR_ID
    ).first()

    if sensor is None:
        db.add(
            Sensor(
                sensor_id=TEMPERATURE_SENSOR_ID,
                name="Living Room Temperature",
                sensor_type="temperature",
                device_id=dht.id,
                unit="celsius",
            )
        )

    humidity = db.query(Sensor).filter(
        Sensor.sensor_id == HUMIDITY_SENSOR_ID
    ).first()

    if humidity is None:
        db.add(
            Sensor(
                sensor_id=HUMIDITY_SENSOR_ID,
                name="Living Room Humidity",
                sensor_type="humidity",
                device_id=dht.id,
                unit="percent",
            )
        )

    db.commit()
