"""
Raw model access for the admin-only POST /admin/predict endpoint.
Takes PaySim-style fields directly, so you can try the model on any input.
"""

from src.schemas.transaction import Transaction
from src.services.fraud.features import (
    build_raw_features,
    current_paysim_step,
    encode_paysim_type,
)
from src.services.fraud.model import decide, predict_probability


def predict_fraud(transaction: Transaction) -> dict:

    features = build_raw_features(
        step=transaction.step if transaction.step is not None else current_paysim_step(),
        amount=transaction.amount,
        old_balance_org=transaction.oldbalanceOrg,
        new_balance_orig=transaction.newbalanceOrig,
        old_balance_dest=transaction.oldbalanceDest,
        new_balance_dest=transaction.newbalanceDest,
        type_encoding=encode_paysim_type(transaction.type),
    )

    probability = predict_probability(features)

    return {
        "risk_score": round(probability, 4),
        "decision": decide(probability).value,
        "features": features,
    }
