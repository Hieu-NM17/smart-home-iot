from sqlalchemy.orm import Session

from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate


def get_rooms(db: Session):
    return db.query(Room).all()


def get_room(db: Session, room_id: int):
    return db.query(Room).filter(Room.id == room_id).first()


def create_room(db: Session, room_data: RoomCreate):
    room = Room(
        name=room_data.name,
        description=room_data.description,
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return room


def update_room(
    db: Session,
    room_id: int,
    room_data: RoomUpdate,
):
    room = get_room(db, room_id)

    if room is None:
        return None

    if room_data.name is not None:
        room.name = room_data.name

    if room_data.description is not None:
        room.description = room_data.description

    db.commit()
    db.refresh(room)

    return room


def delete_room(db: Session, room_id: int):
    room = get_room(db, room_id)

    if room is None:
        return None

    db.delete(room)
    db.commit()

    return room