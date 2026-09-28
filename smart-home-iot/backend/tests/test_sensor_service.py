from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.device import Device
from app.models.room import Room
from app.schemas.sensor import SensorCreate, SensorUpdate
from app.services.sensor_service import (
    get_sensors,
    get_sensor,
    create_sensor,
    update_sensor,
    delete_sensor,
    save_reading,
    get_readings,
)


DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def setup_database():
    Base.metadata.create_all(bind=engine)


def teardown_database():
    Base.metadata.drop_all(bind=engine)


def create_test_device(db):
    room = Room(
        name="living_room",
        description="Living room",
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    device = Device(
        device_id="sensor_device_01",
        name="Environment Device",
        device_type="sensor",
        room_id=room.id,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def test_create_sensor():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    sensor_data = SensorCreate(
        sensor_id="temperature_01",
        name="Temperature Sensor",
        sensor_type="temperature",
        device_id=device.id,
        unit="celsius",
    )

    sensor = create_sensor(db, sensor_data)

    assert sensor.id is not None
    assert sensor.sensor_id == "temperature_01"
    assert sensor.name == "Temperature Sensor"
    assert sensor.sensor_type == "temperature"
    assert sensor.device_id == device.id
    assert sensor.unit == "celsius"

    db.close()
    teardown_database()


def test_get_sensor():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    sensor = create_sensor(
        db,
        SensorCreate(
            sensor_id="temperature_01",
            name="Temperature Sensor",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    result = get_sensor(db, sensor.id)

    assert result is not None
    assert result.id == sensor.id
    assert result.sensor_id == "temperature_01"

    db.close()
    teardown_database()


def test_get_sensors():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    create_sensor(
        db,
        SensorCreate(
            sensor_id="temperature_01",
            name="Temperature Sensor",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    create_sensor(
        db,
        SensorCreate(
            sensor_id="humidity_01",
            name="Humidity Sensor",
            sensor_type="humidity",
            device_id=device.id,
            unit="percent",
        ),
    )

    sensors = get_sensors(db)

    assert len(sensors) == 2

    db.close()
    teardown_database()


def test_update_sensor():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    sensor = create_sensor(
        db,
        SensorCreate(
            sensor_id="temperature_01",
            name="Temperature Sensor",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    updated_sensor = update_sensor(
        db,
        sensor.id,
        SensorUpdate(
            name="Room Temperature",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    assert updated_sensor is not None
    assert updated_sensor.name == "Room Temperature"

    db.close()
    teardown_database()


def test_delete_sensor():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    sensor = create_sensor(
        db,
        SensorCreate(
            sensor_id="temperature_01",
            name="Temperature Sensor",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    deleted_sensor = delete_sensor(db, sensor.id)

    assert deleted_sensor is not None
    assert deleted_sensor.id == sensor.id

    result = get_sensor(db, sensor.id)

    assert result is None

    db.close()
    teardown_database()


def test_save_reading():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    sensor = create_sensor(
        db,
        SensorCreate(
            sensor_id="temperature_01",
            name="Temperature Sensor",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    reading = save_reading(
        db,
        sensor.id,
        25.6,
    )

    assert reading is not None
    assert reading.sensor_id == sensor.id
    assert reading.value == 25.6
    assert reading.recorded_at is not None

    db.close()
    teardown_database()


def test_get_readings():
    setup_database()

    db = TestingSessionLocal()

    device = create_test_device(db)

    sensor = create_sensor(
        db,
        SensorCreate(
            sensor_id="temperature_01",
            name="Temperature Sensor",
            sensor_type="temperature",
            device_id=device.id,
            unit="celsius",
        ),
    )

    save_reading(db, sensor.id, 25.6)
    save_reading(db, sensor.id, 26.1)

    readings = get_readings(db, sensor.id)

    assert readings is not None
    assert len(readings) == 2
    assert readings[0].value == 26.1
    assert readings[1].value == 25.6

    db.close()
    teardown_database()