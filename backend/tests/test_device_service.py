from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.room import Room
from app.schemas.device import DeviceCreate, DeviceUpdate, DeviceCommand
from app.services.device_service import (
    get_devices,
    get_device,
    create_device,
    update_device,
    delete_device,
    send_command,
    update_device_state,
    update_device_online_status,
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


def create_test_room(db):
    room = Room(
        name="living_room",
        description="Living room",
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return room


def test_create_device():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device_data = DeviceCreate(
        device_id="light_01",
        name="Living Room Light",
        device_type="light",
        room_id=room.id,
    )

    device = create_device(db, device_data)

    assert device.id is not None
    assert device.device_id == "light_01"
    assert device.name == "Living Room Light"
    assert device.device_type == "light"
    assert device.room_id == room.id

    db.close()
    teardown_database()


def test_get_device():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device = create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    result = get_device(db, device.id)

    assert result is not None
    assert result.id == device.id
    assert result.device_id == "light_01"

    db.close()
    teardown_database()


def test_get_devices():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    create_device(
        db,
        DeviceCreate(
            device_id="fan_01",
            name="Living Room Fan",
            device_type="fan",
            room_id=room.id,
        ),
    )

    devices = get_devices(db)

    assert len(devices) == 2

    db.close()
    teardown_database()


def test_update_device():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device = create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    updated_device = update_device(
        db,
        device.id,
        DeviceUpdate(
            name="Main Light",
            device_type="lamp",
            room_id=room.id,
        ),
    )

    assert updated_device is not None
    assert updated_device.name == "Main Light"
    assert updated_device.device_type == "lamp"

    db.close()
    teardown_database()


def test_delete_device():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device = create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    deleted_device = delete_device(db, device.id)

    assert deleted_device is not None
    assert deleted_device.id == device.id

    result = get_device(db, device.id)

    assert result is None

    db.close()
    teardown_database()


def test_send_command():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device = create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    result = send_command(
        db,
        device.id,
        DeviceCommand(command="on"),
    )

    assert result is not None
    assert result["topic"] == "home/living_room/light_01/command"
    assert result["payload"] == {"command": "on"}
    assert result["device"].id == device.id

    db.close()
    teardown_database()


def test_update_device_state():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device = create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    updated_device = update_device_state(
        db,
        device.id,
        "on",
    )

    assert updated_device is not None
    assert updated_device.state == "on"

    db.close()
    teardown_database()


def test_update_device_online_status():
    setup_database()

    db = TestingSessionLocal()

    room = create_test_room(db)

    device = create_device(
        db,
        DeviceCreate(
            device_id="light_01",
            name="Living Room Light",
            device_type="light",
            room_id=room.id,
        ),
    )

    updated_device = update_device_online_status(
        db,
        device.id,
        True,
    )

    assert updated_device is not None
    assert updated_device.is_online is True

    db.close()
    teardown_database()