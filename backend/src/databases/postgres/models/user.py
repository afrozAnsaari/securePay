from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.databases.postgres.base import Base

if TYPE_CHECKING:
    from src.databases.postgres.models.upi_profile import UPIProfile
    from src.databases.postgres.models.linked_bank_account import LinkedBankAccount


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    mobile_no: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
    )

    password_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    upi_profiles: Mapped[list["UPIProfile"]] = relationship(
        back_populates="user",
    )

    linked_accounts: Mapped[list["LinkedBankAccount"]] = relationship(
        back_populates="user",
    )
