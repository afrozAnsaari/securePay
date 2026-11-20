from fastapi import APIRouter, Depends

from src.auth.verify_admin import require_admin
from src.schemas.transaction import Transaction
from src.services.fraud.predictor import predict_fraud

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)],
)


@router.post("/predict")
def predict(transaction: Transaction):
    """Run the fraud model on raw PaySim-style input (for demos and debugging)."""

    return predict_fraud(transaction)
