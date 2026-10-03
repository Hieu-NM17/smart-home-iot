from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id"),
        nullable=False,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    sensor: Mapped["Sensor"] = relationship(
        back_populates="readings",
    )