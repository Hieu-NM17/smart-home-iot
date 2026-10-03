from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.services.room_service import (
    create_room,
    delete_room,
    get_room,
    get_rooms,
    update_room,
)

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=list[RoomResponse])
def read_rooms(db: Session = Depends(get_db)):
    return get_rooms(db)


@router.get("/{room_id}", response_model=RoomResponse)
def read_room(room_id: int, db: Session = Depends(get_db)):
    room = get_room(db, room_id)

    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


@router.post("", response_model=RoomResponse, status_code=201)
def add_room(room: RoomCreate, db: Session = Depends(get_db)):
    return create_room(db, room)


@router.put("/{room_id}", response_model=RoomResponse)
def edit_room(
    room_id: int,
    room: RoomUpdate,
    db: Session = Depends(get_db),
):
    updated_room = update_room(db, room_id, room)

    if updated_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    return updated_room


@router.delete("/{room_id}", status_code=204)
def remove_room(room_id: int, db: Session = Depends(get_db)):
    deleted = delete_room(db, room_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Room not found")