from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.databases.postgres.base import Base

if TYPE_CHECKING:
    from src.databases.postgres.models.user import User


class UPIProfile(Base):
    __tablename__ = "upi_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    upi_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="upi_profiles",
    )

    upi_pin_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
