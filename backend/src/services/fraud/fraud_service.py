from decimal import Decimal

from src.databases.postgres.models import Account
from src.schemas.fraud_prediction import FraudPrediction
from src.services.fraud.features import build_transaction_features
from src.services.fraud.model import decide, predict_probability


def predict_transaction(
    sender_account: Account,
    receiver_account: Account,
    amount: Decimal | float,
    transaction_type: str = "P2P",
) -> FraudPrediction:

    features = build_transaction_features(
        sender_account=sender_account,
        receiver_account=receiver_account,
        amount=amount,
        transaction_type=transaction_type,
    )

    probability = predict_probability(features)

    return FraudPrediction(
        risk_score=probability,
        decision=decide(probability).value,
    )
