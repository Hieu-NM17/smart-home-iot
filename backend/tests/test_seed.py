from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.seed import seed_db
from app.models.device import Device
from app.models.room import Room
from app.models.sensor import Sensor

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def test_seed_creates_default_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    seed_db(db)

    room = db.query(Room).one()
    light = db.query(Device).filter(Device.device_id == "light_01").one()
    dht = db.query(Device).filter(Device.device_id == "dht22_01").one()
    sensor = db.query(Sensor).filter(Sensor.sensor_id == "temperature_01").one()
    humidity = db.query(Sensor).filter(Sensor.sensor_id == "humidity_01").one()

    assert humidity.device_id == dht.id
    assert humidity.unit == "percent"
    assert room.name.lower().replace(" ", "_") == "living_room"
    assert light.room_id == room.id
    assert sensor.sensor_id == "temperature_01"
    assert sensor.device_id == dht.id

    db.close()
    Base.metadata.drop_all(bind=engine)


def test_seed_is_idempotent():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    seed_db(db)
    seed_db(db)

    assert db.query(Room).count() == 1
    assert db.query(Device).count() == 2
    assert db.query(Sensor).count() == 2

    db.close()
    Base.metadata.drop_all(bind=engine)


def test_seed_adds_missing_humidity_sensor_to_existing_data():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    seed_db(db)
    db.query(Sensor).filter(Sensor.sensor_id == "humidity_01").delete()
    db.commit()

    seed_db(db)

    assert db.query(Sensor).count() == 2

    db.close()
    Base.metadata.drop_all(bind=engine)
