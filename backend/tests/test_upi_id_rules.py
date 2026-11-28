"""
Every UPI ID that can be created must also be able to receive money.
(Regression: IDs of 1-3 characters used to be accepted at creation but
rejected by the payment code, so nobody could ever pay them by UPI ID.)
"""

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.schemas.upi_profile import UPIProfileCreate
from src.services.payment.input_validator import resolve_receiver


@pytest.mark.parametrize("upi_id", ["a", "jo", "bob", "bob@securepay"])
def test_too_short_upi_id_is_rejected_at_creation(upi_id):
    with pytest.raises(ValidationError, match="at least 4 characters"):
        UPIProfileCreate(upi_id=upi_id, upi_pin="1234")


@pytest.mark.parametrize("upi_id", ["bobb", "a" * 16])
def test_boundary_lengths_are_accepted(upi_id):
    UPIProfileCreate(upi_id=upi_id, upi_pin="1234")


def test_too_short_receiver_gets_clear_message(db):
    with pytest.raises(HTTPException) as exc:
        resolve_receiver(db, "bob@securepay")
    assert exc.value.status_code == 400
    assert exc.value.detail == "UPI ID must be at least 4 characters."


def test_shortest_allowed_upi_id_can_receive_money(client, db, make_person):
    from tests.conftest import UPI_PIN

    sender = make_person("alice", "5000.00")
    receiver = make_person("bobb", "1000.00")

    response = client.post(
        "/upi/pay",
        json={
            "receiver": receiver["upi_id"],
            "sender_upi_profile_id": sender["profile_id"],
            "sender_account_id": sender["account_id"],
            "amount": "100.00",
            "upi_pin": UPI_PIN,
        },
        headers={"Authorization": f"Bearer {sender['token']}", "Idempotency-Key": "k"},
    )
    assert response.status_code == 200, response.text
