"""
Double-spend protection.

Two payments from the same account arrive at the same moment, and together
they cost more than the balance. Both pass the early (unlocked) balance
check, so only the row lock and the re-check under the lock can stop the
second one. Exactly one must succeed, and no money may be created or lost.
"""

import threading
from decimal import Decimal

from fastapi import HTTPException

from src.databases.postgres.database import SessionLocal
from src.databases.postgres.models import Account, LedgerEntry, Payment, User
from src.schemas.payment import PaymentCreate
from src.services.payment.payment_service import process_payment_transaction
from tests.conftest import UPI_PIN


def _pay_in_own_session(sender, receiver_upi, amount, barrier, results):
    session = SessionLocal()
    try:
        user = session.get(User, sender["user_id"])
        barrier.wait()  # release every thread at the same instant
        process_payment_transaction(
            db=session,
            payment_data=PaymentCreate(
                receiver=receiver_upi,
                sender_upi_profile_id=sender["profile_id"],
                sender_account_id=sender["account_id"],
                amount=Decimal(amount),
                upi_pin=UPI_PIN,
            ),
            current_user=user,
        )
        session.commit()
        results.append("ok")
    except HTTPException as exc:
        session.rollback()
        results.append(exc.detail)
    except Exception as exc:  # surface anything unexpected in the assertion
        session.rollback()
        results.append(repr(exc))
    finally:
        session.close()


def test_concurrent_payments_cannot_overspend(db, make_person):
    sender = make_person("alice", "5000.00")
    receiver = make_person("bobby", "1000.00")

    attempts = 4
    barrier = threading.Barrier(attempts)
    results: list = []
    threads = [
        threading.Thread(
            target=_pay_in_own_session,
            args=(sender, receiver["upi_id"], "3000.00", barrier, results),
        )
        for _ in range(attempts)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert results.count("ok") == 1, results
    assert results.count("Insufficient Balance. Transaction Denied") == attempts - 1, results

    db.expire_all()
    sender_balance = db.get(Account, sender["account_id"]).balance
    receiver_balance = db.get(Account, receiver["account_id"]).balance

    assert sender_balance == Decimal("2000.00")
    assert receiver_balance == Decimal("4000.00")
    # No money created or destroyed.
    assert sender_balance + receiver_balance == Decimal("6000.00")

    assert db.query(Payment).count() == 1
    assert db.query(LedgerEntry).count() == 2


def test_opposite_direction_payments_do_not_deadlock(db, make_person):
    """A pays B while B pays A: locks are taken in id order, so both finish."""
    alice = make_person("alice", "5000.00")
    bob = make_person("bobby", "5000.00")

    barrier = threading.Barrier(2)
    results: list = []
    threads = [
        threading.Thread(target=_pay_in_own_session, args=(alice, bob["upi_id"], "700.00", barrier, results)),
        threading.Thread(target=_pay_in_own_session, args=(bob, alice["upi_id"], "300.00", barrier, results)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)

    assert results == ["ok", "ok"], results

    db.expire_all()
    assert db.get(Account, alice["account_id"]).balance == Decimal("4600.00")
    assert db.get(Account, bob["account_id"]).balance == Decimal("5400.00")
