from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate
from app.services.room_service import (
    get_rooms,
    get_room,
    create_room,
    update_room,
    delete_room,
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


def test_create_room():
    setup_database()

    db = TestingSessionLocal()

    room_data = RoomCreate(
        name="Living Room",
        description="Main living room",
    )

    room = create_room(db, room_data)

    assert room.id is not None
    assert room.name == "Living Room"
    assert room.description == "Main living room"

    db.close()
    teardown_database()


def test_get_room():
    setup_database()

    db = TestingSessionLocal()

    room_data = RoomCreate(
        name="Bedroom",
        description="Main bedroom",
    )

    created_room = create_room(db, room_data)

    room = get_room(db, created_room.id)

    assert room is not None
    assert room.id == created_room.id
    assert room.name == "Bedroom"

    db.close()
    teardown_database()


def test_get_rooms():
    setup_database()

    db = TestingSessionLocal()

    create_room(
        db,
        RoomCreate(
            name="Living Room",
            description="Living room",
        ),
    )

    create_room(
        db,
        RoomCreate(
            name="Bedroom",
            description="Bedroom",
        ),
    )

    rooms = get_rooms(db)

    assert len(rooms) == 2

    db.close()
    teardown_database()


def test_update_room():
    setup_database()

    db = TestingSessionLocal()

    room = create_room(
        db,
        RoomCreate(
            name="Living Room",
            description="Old description",
        ),
    )

    updated_room = update_room(
        db,
        room.id,
        RoomUpdate(
            name="New Living Room",
            description="New description",
        ),
    )

    assert updated_room is not None
    assert updated_room.name == "New Living Room"
    assert updated_room.description == "New description"

    db.close()
    teardown_database()


def test_delete_room():
    setup_database()

    db = TestingSessionLocal()

    room = create_room(
        db,
        RoomCreate(
            name="Room to Delete",
            description="Temporary room",
        ),
    )

    deleted_room = delete_room(db, room.id)

    assert deleted_room is not None
    assert deleted_room.id == room.id

    result = get_room(db, room.id)

    assert result is None

    db.close()
    teardown_database()