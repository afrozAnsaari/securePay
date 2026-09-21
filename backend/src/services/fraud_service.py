import json
import joblib


from pathlib import Path

from src.utils.enums.FraudDecision import FraudDecision

from src.databases.models import Account

from src.data.preprocess import preprocess_transaction

from src.services.features import build_transaction_features

from src.schemas.fraud_prediction import FraudPrediction

BASE_DIR = Path(__file__).resolve().parents[3]
# print(BASE_DIR)

MODEL = joblib.load(BASE_DIR / "models" / "paysim" / "xgboost_paysim_model.joblib")

with open(BASE_DIR / "models" / "paysim" / "config.json") as f:
    CONFIG = json.load(f)

THRESHOLD = CONFIG["threshold"]


def predict_transaction(
    sender_account: Account,
    receiver_account: Account,
    amount: float,
    transaction_type: str = "P2P",
) -> FraudPrediction:

    features = build_transaction_features(
        sender_account=sender_account,
        receiver_account=receiver_account,
        amount=amount,
        transaction_type=transaction_type,
    )

    df = preprocess_transaction(features)

    try:
        probability: float = float(MODEL.predict_proba(df)[0][1])
    except Exception as e:
        raise RuntimeError("Fraud prediction failed.") from e

    if 0.00 <= probability <= 0.40:
        decision = FraudDecision.APPROVED.value
    elif 0.40 < probability < THRESHOLD:
        decision = FraudDecision.REVIEW.value
    elif THRESHOLD <= probability:
        decision = FraudDecision.DECLINED.value
    else:
        raise RuntimeError("Invalid values returned by the model.")

    return FraudPrediction(
        risk_score=probability,
        decision=decision,
    )


# print(FraudDecision.APPROVED)
