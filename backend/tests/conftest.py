"""
Shared test setup.

The tests need a real Postgres and Redis, because what they check (row
locks, unique constraints, Redis caching) only exists there. They use
their OWN database and Redis DB number, never the app's:

    TEST_DATABASE_URL  default postgresql+psycopg2://securepay:securepay@localhost:5433/securepay_test
    TEST_REDIS_URL     default redis://localhost:6380/15

The database name must end in "_test"; it is created if missing, migrated
with Alembic, and wiped between tests.

Run (from backend/):  pytest
"""

import os
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://securepay:securepay@localhost:5433/securepay_test",
)
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/15")

_db_name = make_url(TEST_DATABASE_URL).database or ""
if not _db_name.endswith("_test"):
    raise RuntimeError(
        f"Refusing to run tests against database {_db_name!r}: "
        "TEST_DATABASE_URL must point to a database whose name ends in '_test', "
        "because the tests delete all of its data."
    )

# These must be set before anything from src/ is imported, because
# src.config.settings reads them at import time. They override backend/.env.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-" + "x" * 40)
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key-" + "x" * 40)
os.environ.setdefault(
    # A fixed, valid Fernet key used only by the tests.
    "ENCRYPTION_KEY",
    "Qm9Lc3B0ZXN0a2V5Zm9yc2VjdXJlcGF5dGVzdHMwMDA=",
)


def _create_test_database_if_missing() -> None:
    url = make_url(TEST_DATABASE_URL)
    admin_engine = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": url.database},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    """Create the test database and run every migration once per test run."""
    from alembic import command
    from alembic.config import Config

    _create_test_database_if_missing()

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def clean_state(migrated_database):
    """Every test starts with empty tables and an empty Redis DB."""
    from src.databases.postgres.database import engine
    from src.databases.postgres.models import Base
    from src.databases.redis import redis_client

    tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    redis_client.flushdb()
    yield


@pytest.fixture
def db():
    from src.databases.postgres.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from src.api.app import app

    with TestClient(app) as test_client:
        yield test_client


UPI_PIN = "1234"
CARD_PIN = "1111"

_counter = {"n": 0}


@pytest.fixture
def make_person(db):
    """
    Create a full fake person: bank customer, account with `balance`,
    app user, UPI profile and the account linked as primary.
    Returns a dict with the ids the payment API needs.
    """
    from datetime import date

    from src.auth.jwt import create_access_token
    from src.databases.postgres.crud import (
        create_account,
        create_card,
        create_customer,
        create_upi_profile,
        create_user,
        link_bank_acc,
    )
    from src.databases.postgres.models import User
    from src.schemas.account import AccountCreate
    from src.schemas.card import CardCreate
    from src.schemas.customer import CustomerCreate
    from src.schemas.link_bank_request import LinkBankRequest
    from src.schemas.upi_profile import UPIProfileCreate
    from src.schemas.user import UserCreate

    def _make(upi: str, balance: str) -> dict:
        _counter["n"] += 1
        n = _counter["n"]
        mobile = f"90000{n:05d}"
        email = f"{upi}@example.com"

        customer = create_customer(
            db,
            CustomerCreate(
                full_name=f"Test {upi.title()}",
                dob=date(1990, 1, 1),
                mobile_no=mobile,
                email=email,
                aadhar_no=f"2000000{n:05d}",
                pan_no=f"AAAPT{n:04d}A",
                address="Test Street",
            ),
        )
        create_user(
            db,
            UserCreate(name=f"Test {upi.title()}", mobile_no=mobile, email=email, password="123456"),
        )
        user = db.query(User).filter(User.mobile_no == mobile).one()
        profile = create_upi_profile(db, UPIProfileCreate(upi_id=upi, upi_pin=UPI_PIN), user)

        account = create_account(
            db,
            AccountCreate(
                customer_id=customer.id,
                bank_name="SBI",
                account_type="SAVINGS",
                initial_balance=Decimal(balance),
                mobile_no=mobile,
            ),
        )
        card = create_card(CardCreate(account_id=account.id, network="RUPAY", card_pin=CARD_PIN), db)
        link_bank_acc(
            LinkBankRequest(
                bank_name="SBI",
                card_number=card["card_number"],
                expiry_month=card["expiry_month"],
                expiry_year=card["expiry_year"],
                card_pin=CARD_PIN,
            ),
            db,
            user,
        )
        db.commit()

        return {
            "user_id": user.id,
            "upi_id": f"{upi}@securepay",
            "profile_id": profile["profile_id"],
            "account_id": account.id,
            "token": create_access_token({"user_id": user.id}),
        }

    return _make
