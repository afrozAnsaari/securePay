"""How a fraud probability becomes a decision (thresholds from models/paysim/config.json)."""

import pytest

from src.services.fraud.model import DECLINE_THRESHOLD, REVIEW_THRESHOLD, decide
from src.utils.enums.FraudDecision import FraudDecision


def test_thresholds_are_ordered():
    assert 0.0 <= REVIEW_THRESHOLD < DECLINE_THRESHOLD <= 1.0


@pytest.mark.parametrize(
    "probability, expected",
    [
        (0.0, FraudDecision.APPROVED),
        (REVIEW_THRESHOLD, FraudDecision.APPROVED),          # equal to review -> still approved
        (REVIEW_THRESHOLD + 1e-6, FraudDecision.REVIEW),
        (DECLINE_THRESHOLD - 1e-6, FraudDecision.REVIEW),
        (DECLINE_THRESHOLD, FraudDecision.DECLINED),         # equal to decline -> declined
        (1.0, FraudDecision.DECLINED),
    ],
)
def test_decision_boundaries(probability, expected):
    assert decide(probability) == expected


def test_declined_payment_moves_no_money(client, db, make_person, monkeypatch):
    """When the model declines, the API returns 403 and balances are untouched."""
    from decimal import Decimal

    from src.databases.postgres.models import Account, Payment
    from src.schemas.fraud_prediction import FraudPrediction
    from src.services.payment import payment_service
    from tests.conftest import UPI_PIN

    monkeypatch.setattr(
        payment_service,
        "predict_transaction",
        lambda **_: FraudPrediction(risk_score=0.99, decision=FraudDecision.DECLINED.value),
    )

    sender = make_person("alice", "5000.00")
    receiver = make_person("bobby", "1000.00")

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

    assert response.status_code == 403
    assert db.query(Payment).count() == 0
    assert db.get(Account, sender["account_id"]).balance == Decimal("5000.00")
