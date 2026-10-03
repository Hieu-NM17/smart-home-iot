from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.sensor import Sensor

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    device_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    device_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(20),
        default="off",
        nullable=False,
    )

    is_online: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    room: Mapped["Room"] = relationship(
        back_populates="devices",
    )

    sensors: Mapped[list["Sensor"]] = relationship(
    back_populates="device",
    cascade="all, delete-orphan",
    )