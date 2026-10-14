from datetime import datetime, date, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Date,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
)

from src.utils.enums.BankName import BankName
from src.utils.enums.AccountType import AccountType
from src.utils.enums.CardNetwork import CardNetwork
from src.utils.enums.CardStatus import CardStatus
from src.utils.enums.AccountStatus import AccountStatus

from sqlalchemy.sql import func
from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column,
)

from src.databases.database import Base


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


class Merchant(Base):

    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    api_key: Mapped[str] = mapped_column(
        String,
        unique=True,
        index=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )


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
        Float,
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
        String(10),
        unique=True,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            name="uq_payments_transaction_id",
        ),
    )


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

    balance: Mapped[float] = mapped_column(
        Float,
        default=0,
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
        Float,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=func.now(),
    )


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

    # linked_accounts: Mapped[list["LinkedBankAccount"]] = relationship(
    #     back_populates="upi_profile",
    # )

    upi_pin_hash: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )


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
