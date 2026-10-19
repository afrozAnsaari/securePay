from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.databases.postgres.base import Base
from src.utils.enums.CardNetwork import CardNetwork
from src.utils.enums.CardStatus import CardStatus

if TYPE_CHECKING:
    from src.databases.postgres.models.account import Account


class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
    )

    card_number_hash: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    card_number_encrypted: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    last4: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )

    expiry_month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    expiry_year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    network: Mapped[CardNetwork] = mapped_column(
        SQLEnum(CardNetwork),
        nullable=False,
    )

    status: Mapped[CardStatus] = mapped_column(
        SQLEnum(CardStatus),
        default=CardStatus.ACTIVE.value,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
    )

    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="cards",
    )

    card_pin_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
