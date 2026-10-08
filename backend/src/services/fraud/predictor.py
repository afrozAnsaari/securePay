import joblib
import json

from pathlib import Path

from src.data.preprocess import preprocess_transaction

# NEW_BASE_DIR=Path.cwd()

# print(NEW_BASE_DIR)

BASE_DIR = Path(__file__).resolve().parents[3]

# print(BASE_DIR)

model = joblib.load(
    BASE_DIR / "src" / "models" / "paysim" / "xgboost_paysim_model.joblib"
)

with open(BASE_DIR / "src" / "models" / "paysim" / "config.json") as f:
    config = json.load(f)


THRESHOLD = config["threshold"]


# The actual func that performs the payment classification
def predict_fraud(transaction):

    data = preprocess_transaction(transaction)

    # print(data)

    probability = model.predict_proba(data)[0][1]

    # print(probability)

    if probability >= THRESHOLD:
        decision = "BLOCK"

    elif probability >= 0.5:
        decision = "REVIEW"

    else:
        decision = "ALLOW"

    return {"risk_score": round(float(probability), 4), "decision": decision}


# if __name__ == "__main__":
# print(BASE_DIR)
