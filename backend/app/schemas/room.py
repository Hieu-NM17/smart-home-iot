from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RoomCreate(BaseModel):
    name: str
    description: str | None = None


class RoomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoomResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)