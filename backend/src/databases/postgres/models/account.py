from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.databases.postgres.base import Base
from src.utils.enums.AccountStatus import AccountStatus
from src.utils.enums.AccountType import AccountType
from src.utils.enums.BankName import BankName

if TYPE_CHECKING:
    from src.databases.postgres.models.card import Card
    from src.databases.postgres.models.customer import Customer
    from src.databases.postgres.models.linked_bank_account import LinkedBankAccount


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    account_number: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    bank_name: Mapped[BankName] = mapped_column(
        SQLEnum(BankName),
        nullable=False,
    )

    ifsc_code: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    account_type: Mapped[AccountType] = mapped_column(
        SQLEnum(AccountType),
        nullable=False,
    )

    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    mobile_no: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    status: Mapped[AccountStatus] = mapped_column(
        SQLEnum(AccountStatus),
        default=AccountStatus.ACTIVE.value,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="accounts",
    )

    cards: Mapped[list["Card"]] = relationship(
        "Card",
        back_populates="account",
    )

    linked_accounts: Mapped[list["LinkedBankAccount"]] = relationship(
        back_populates="account",
    )
