from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.mqtt.deps import get_publisher
from app.mqtt.publisher import MQTTPublisher
from app.schemas.device import (
    DeviceCommand,
    DeviceCreate,
    DeviceResponse,
    DeviceUpdate,
)
from app.services.device_service import (
    create_device,
    delete_device,
    get_device,
    get_devices,
    send_command,
    update_device,
    update_device_online_status,
    update_device_state,
)

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceResponse])
def read_devices(db: Session = Depends(get_db)):
    return get_devices(db)


@router.get("/{device_id}", response_model=DeviceResponse)
def read_device(device_id: int, db: Session = Depends(get_db)):
    device = get_device(db, device_id)

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@router.post("", response_model=DeviceResponse, status_code=201)
def add_device(device: DeviceCreate, db: Session = Depends(get_db)):
    return create_device(db, device)


@router.put("/{device_id}", response_model=DeviceResponse)
def edit_device(
    device_id: int,
    device: DeviceUpdate,
    db: Session = Depends(get_db),
):
    updated_device = update_device(db, device_id, device)

    if updated_device is None:
        raise HTTPException(status_code=404, detail="Device not found")

    return updated_device

@router.post("/{device_id}/command")
def command_device(
    device_id: int,
    command: DeviceCommand,
    db: Session = Depends(get_db),
    publisher: MQTTPublisher | None = Depends(get_publisher),
):
    result = send_command(db, device_id, command)

    if result is None:
        raise HTTPException(status_code=404, detail="Device not found")

    if publisher is None or not publisher.is_connected():
        raise HTTPException(
            status_code=503,
            detail="MQTT broker is not connected",
        )

    # The ESP32 compares the raw payload with "on" / "off" (not JSON).
    publisher.publish(result["topic"], command.command)

    return result


@router.delete("/{device_id}", status_code=204)
def remove_device(device_id: int, db: Session = Depends(get_db)):
    deleted = delete_device(db, device_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Device not found")