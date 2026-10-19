from __future__ import annotations
from datetime import datetime, date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.databases.postgres.base import Base

if TYPE_CHECKING:
    from src.databases.postgres.models.account import Account


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    dob: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    mobile_no: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    aadhar_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    aadhar_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    pan_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    pan_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    kyc_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
    )

    accounts: Mapped[list["Account"]] = relationship(
        "Account",
        back_populates="customer",
    )
