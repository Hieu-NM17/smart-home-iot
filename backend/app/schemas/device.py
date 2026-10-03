from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreate(BaseModel):
    device_id: str
    name: str
    device_type: str
    room_id: int


class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type: str | None = None
    room_id: int | None = None


class DeviceCommand(BaseModel):
    command: str = Field(pattern="^(on|off)$")


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    name: str
    device_type: str
    room_id: int
    state: str
    is_online: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)