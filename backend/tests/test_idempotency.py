"""
Idempotency: retrying a payment with the same Idempotency-Key must never
charge twice, whether the answer comes from Redis or from Postgres.
"""

from decimal import Decimal

from src.databases.postgres.models import Account, Payment
from src.databases.redis import redis_client
from tests.conftest import UPI_PIN


def _pay(client, sender, receiver_upi, amount, key):
    return client.post(
        "/upi/pay",
        json={
            "receiver": receiver_upi,
            "sender_upi_profile_id": sender["profile_id"],
            "sender_account_id": sender["account_id"],
            "amount": amount,
            "upi_pin": UPI_PIN,
        },
        headers={"Authorization": f"Bearer {sender['token']}", "Idempotency-Key": key},
    )


def test_retry_with_same_key_returns_same_payment(client, db, make_person):
    sender = make_person("alice", "5000.00")
    receiver = make_person("bobby", "1000.00")

    first = _pay(client, sender, receiver["upi_id"], "250.00", "key-1")
    assert first.status_code == 200, first.text
    assert first.json()["message"] == "Payment successful."

    # Same request again: answered from the Redis cache.
    second = _pay(client, sender, receiver["upi_id"], "250.00", "key-1")
    assert second.status_code == 200, second.text
    assert second.json()["transaction_id"] == first.json()["transaction_id"]

    assert db.query(Payment).count() == 1
    assert db.get(Account, sender["account_id"]).balance == Decimal("4750.00")


def test_retry_after_redis_is_wiped_uses_postgres(client, db, make_person):
    sender = make_person("alice", "5000.00")
    receiver = make_person("bobby", "1000.00")

    first = _pay(client, sender, receiver["upi_id"], "250.00", "key-1")
    assert first.status_code == 200, first.text

    redis_client.flushdb()  # simulate Redis restart / expiry

    retry = _pay(client, sender, receiver["upi_id"], "250.00", "key-1")
    assert retry.status_code == 200, retry.text
    assert retry.json()["transaction_id"] == first.json()["transaction_id"]
    assert retry.json()["message"] == "Payment already processed."

    assert db.query(Payment).count() == 1


def test_same_key_for_different_payment_is_rejected(client, db, make_person):
    sender = make_person("alice", "5000.00")
    receiver = make_person("bobby", "1000.00")

    assert _pay(client, sender, receiver["upi_id"], "250.00", "key-1").status_code == 200

    reused = _pay(client, sender, receiver["upi_id"], "999.00", "key-1")
    assert reused.status_code == 409

    assert db.query(Payment).count() == 1


def test_different_keys_are_different_payments(client, db, make_person):
    sender = make_person("alice", "5000.00")
    receiver = make_person("bobby", "1000.00")

    assert _pay(client, sender, receiver["upi_id"], "250.00", "key-1").status_code == 200
    assert _pay(client, sender, receiver["upi_id"], "250.00", "key-2").status_code == 200

    assert db.query(Payment).count() == 2
    assert db.get(Account, sender["account_id"]).balance == Decimal("4500.00")
