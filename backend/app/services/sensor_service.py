from sqlalchemy.orm import Session

from app.models.sensor import Sensor
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.schemas.sensor import SensorCreate, SensorUpdate


def get_sensors(db: Session):
    return db.query(Sensor).all()


def get_sensor(db: Session, sensor_id: int):
    return db.query(Sensor).filter(Sensor.id == sensor_id).first()


def get_sensor_by_sensor_id(db: Session, sensor_id: str):
    return db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()


def create_sensor(db: Session, sensor_data: SensorCreate):
    sensor = Sensor(
        sensor_id=sensor_data.sensor_id,
        name=sensor_data.name,
        sensor_type=sensor_data.sensor_type,
        device_id=sensor_data.device_id,
        unit=sensor_data.unit,
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return sensor


def update_sensor(
    db: Session,
    sensor_id: int,
    sensor_data: SensorUpdate,
):
    sensor = get_sensor(db, sensor_id)

    if sensor is None:
        return None

    if sensor_data.name is not None:
        sensor.name = sensor_data.name

    if sensor_data.sensor_type is not None:
        sensor.sensor_type = sensor_data.sensor_type

    if sensor_data.device_id is not None:
        sensor.device_id = sensor_data.device_id

    if sensor_data.unit is not None:
        sensor.unit = sensor_data.unit

    db.commit()
    db.refresh(sensor)

    return sensor


def delete_sensor(db: Session, sensor_id: int):
    sensor = get_sensor(db, sensor_id)

    if sensor is None:
        return None

    db.delete(sensor)
    db.commit()

    return sensor


def save_reading(
    db: Session,
    sensor_id: int,
    value: float,
):
    sensor = get_sensor(db, sensor_id)

    if sensor is None:
        return None

    reading = SensorReading(
        sensor_id=sensor.id,
        value=value,
    )

    db.add(reading)
    db.commit()
    db.refresh(reading)

    return reading


def get_readings(
    db: Session,
    sensor_id: int,
    limit: int | None = None,
):
    sensor = get_sensor(db, sensor_id)

    if sensor is None:
        return None

    query = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id
    ).order_by(SensorReading.id.desc())

    if limit is not None:
        query = query.limit(limit)

    return query.all()
