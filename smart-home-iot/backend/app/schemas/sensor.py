from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SensorCreate(BaseModel):
    sensor_id: str
    name: str
    sensor_type: str
    device_id: int
    unit: str


class SensorUpdate(BaseModel):
    name: str | None = None
    sensor_type: str | None = None
    device_id: int | None = None
    unit: str | None = None


class SensorReadingCreate(BaseModel):
    value: float


class SensorResponse(BaseModel):
    id: int
    sensor_id: str
    name: str
    sensor_type: str
    device_id: int
    unit: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorReadingResponse(BaseModel):
    id: int
    sensor_id: int
    value: float
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)