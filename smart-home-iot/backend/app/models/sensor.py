from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    sensor_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    sensor_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    device: Mapped["Device"] = relationship(
        back_populates="sensors",
    )

    readings: Mapped[list["SensorReading"]] = relationship(
        back_populates="sensor",
        cascade="all, delete-orphan",
    )