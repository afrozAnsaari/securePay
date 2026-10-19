from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.databases.postgres.base import Base

if TYPE_CHECKING:
    from src.databases.postgres.models.account import Account
    from src.databases.postgres.models.user import User


class LinkedBankAccount(Base):
    __tablename__ = "linked_bank_accounts"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    linked_at: Mapped[datetime] = mapped_column(
        default=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="linked_accounts",
    )

    account: Mapped["Account"] = relationship(
        back_populates="linked_accounts",
    )
