"""
Loads the trained PaySim XGBoost model once and turns a probability into
a business decision. Every fraud check in the app goes through here.
"""

import json
from pathlib import Path

import joblib
import pandas as pd

from src.utils.enums.FraudDecision import FraudDecision
from src.utils.feature_columns import FEATURE_COLUMNS

MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "paysim"

MODEL = joblib.load(MODEL_DIR / "xgboost_paysim_model.joblib")

with open(MODEL_DIR / "config.json") as f:
    _CONFIG = json.load(f)

# probability >= DECLINE_THRESHOLD  -> DECLINED
# probability >  REVIEW_THRESHOLD   -> REVIEW
# otherwise                         -> APPROVED
DECLINE_THRESHOLD: float = float(_CONFIG["threshold"])
REVIEW_THRESHOLD: float = float(_CONFIG.get("review_threshold", 0.4))

if not 0.0 <= REVIEW_THRESHOLD < DECLINE_THRESHOLD <= 1.0:
    raise RuntimeError(
        "models/paysim/config.json: need 0 <= review_threshold < threshold <= 1"
    )


def predict_probability(features: dict) -> float:
    df = pd.DataFrame([features])[FEATURE_COLUMNS]

    try:
        probability = float(MODEL.predict_proba(df)[0][1])
    except Exception as e:
        raise RuntimeError("Fraud prediction failed.") from e

    if not 0.0 <= probability <= 1.0:
        raise RuntimeError("Invalid values returned by the model.")

    return probability


def decide(probability: float) -> FraudDecision:
    if probability >= DECLINE_THRESHOLD:
        return FraudDecision.DECLINED
    if probability > REVIEW_THRESHOLD:
        return FraudDecision.REVIEW
    return FraudDecision.APPROVED
