from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.room import Room
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceCommand,
)


def get_devices(db: Session):
    return db.query(Device).all()


def get_device(db: Session, device_id: int):
    return db.query(Device).filter(Device.id == device_id).first()


def get_device_by_device_id(db: Session, device_id: str):
    return db.query(Device).filter(Device.device_id == device_id).first()


def create_device(db: Session, device_data: DeviceCreate):
    device = Device(
        device_id=device_data.device_id,
        name=device_data.name,
        device_type=device_data.device_type,
        room_id=device_data.room_id,
    )

    db.add(device)
    db.commit()
    db.refresh(device)

    return device


def update_device(
    db: Session,
    device_id: int,
    device_data: DeviceUpdate,
):
    device = get_device(db, device_id)

    if device is None:
        return None

    if device_data.name is not None:
        device.name = device_data.name

    if device_data.device_type is not None:
        device.device_type = device_data.device_type

    if device_data.room_id is not None:
        device.room_id = device_data.room_id

    db.commit()
    db.refresh(device)

    return device


def delete_device(db: Session, device_id: int):
    device = get_device(db, device_id)

    if device is None:
        return None

    db.delete(device)
    db.commit()

    return device


def send_command(
    db: Session,
    device_id: int,
    command_data: DeviceCommand,
):
    device = get_device(db, device_id)

    if device is None:
        return None

    room = db.query(Room).filter(Room.id == device.room_id).first()

    if room is None:
        return None

    room_name = room.name.lower().replace(" ", "_")
    topic = f"home/{room_name}/{device.device_id}/command"

    payload = {
        "command": command_data.command
    }

    return {
        "device": device,
        "topic": topic,
        "payload": payload,
    }


def update_device_state(
    db: Session,
    device_id: int,
    state: str,
):
    device = get_device(db, device_id)

    if device is None:
        return None

    if state not in ("on", "off"):
        raise ValueError("Invalid device state")

    device.state = state

    db.commit()
    db.refresh(device)

    return device


def update_device_online_status(
    db: Session,
    device_id: int,
    is_online: bool,
):
    device = get_device(db, device_id)

    if device is None:
        return None

    device.is_online = is_online

    db.commit()
    db.refresh(device)

    return device