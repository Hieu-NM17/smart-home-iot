from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.schemas.sensor import (
    SensorCreate,
    SensorReadingCreate,
    SensorReadingResponse,
    SensorResponse,
    SensorUpdate,
)
from app.services.sensor_service import (
    create_sensor,
    delete_sensor,
    get_sensor,
    get_sensors,
    get_readings,
    save_reading,
    update_sensor,
)

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("", response_model=list[SensorResponse])
def read_sensors(db: Session = Depends(get_db)):
    return get_sensors(db)


@router.get("/{sensor_id}", response_model=SensorResponse)
def read_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = get_sensor(db, sensor_id)

    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return sensor


@router.post("", response_model=SensorResponse, status_code=201)
def add_sensor(sensor: SensorCreate, db: Session = Depends(get_db)):
    return create_sensor(db, sensor)


@router.put("/{sensor_id}", response_model=SensorResponse)
def edit_sensor(
    sensor_id: int,
    sensor: SensorUpdate,
    db: Session = Depends(get_db),
):
    updated_sensor = update_sensor(db, sensor_id, sensor)

    if updated_sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return updated_sensor


@router.delete("/{sensor_id}", status_code=204)
def remove_sensor(sensor_id: int, db: Session = Depends(get_db)):
    deleted = delete_sensor(db, sensor_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Sensor not found")


@router.get("/{sensor_id}/readings")
def read_sensor_readings(
    sensor_id: int,
    limit: int | None = Query(None, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    sensor = get_sensor(db, sensor_id)

    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return get_readings(db, sensor_id, limit)


@router.post("/{sensor_id}/readings", response_model=SensorReadingResponse)
def add_sensor_reading(
    sensor_id: int,
    reading: SensorReadingCreate,
    db: Session = Depends(get_db),
):
    result = save_reading(db, sensor_id, reading.value)

    if result is None:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return result