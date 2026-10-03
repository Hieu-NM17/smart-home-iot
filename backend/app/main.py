from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import rooms, devices, sensors
from app.database.database import SessionLocal
from app.database.init_db import init_db
from app.database.seed import seed_db
from app.mqtt.client import MQTTClient
from app.mqtt.deps import set_publisher
from app.mqtt.handlers import handle_message
from app.mqtt.publisher import MQTTPublisher

# smart-home-iot/frontend (this file is smart-home-iot/backend/app/main.py)
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(
    title="Smart Home IoT API",
    version="1.0.0",
)

mqtt_client = MQTTClient()
mqtt_client.message_handler = handle_message
mqtt_client.add_subscription("home/+/+/state")
mqtt_client.add_subscription("home/+/+/sensor")
mqtt_client.add_subscription("home/+/+/status")
set_publisher(MQTTPublisher(mqtt_client))

app.include_router(rooms.router)
app.include_router(devices.router)
app.include_router(sensors.router)

# Must stay last: "/" would otherwise shadow the API routes above.
if FRONTEND_DIR.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIR, html=True),
        name="frontend",
    )


@app.on_event("startup")
def startup():
    init_db()

    with SessionLocal() as db:
        seed_db(db)

    mqtt_client.connect()
    mqtt_client.start_loop()


@app.on_event("shutdown")
def shutdown():
    mqtt_client.stop_loop()
    mqtt_client.disconnect()
