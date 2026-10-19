from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Numeric,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)

from src.databases.postgres.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    sender_upi_profile_id = Column(
        Integer,
        ForeignKey("upi_profiles.id"),
        nullable=False,
    )

    receiver_upi_profile_id = Column(
        Integer,
        ForeignKey("upi_profiles.id"),
        nullable=False,
    )

    sender_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    receiver_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
    )

    transaction_type = Column(
        String,
        nullable=False,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
    )

    risk_score = Column(Float)

    fraud_decision = Column(String)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
    )

    transaction_id = Column(
        String(12),
        unique=True,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            name="uq_payments_transaction_id",
        ),
        CheckConstraint(
            "LENGTH(transaction_id) = 12",
            name="chk_transaction_id_length",
        ),
    )
