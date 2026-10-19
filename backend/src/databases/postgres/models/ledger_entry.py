from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.sql import func

from src.databases.postgres.base import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
    )

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
    )

    entry_type = Column(
        String,
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=func.now(),
    )
