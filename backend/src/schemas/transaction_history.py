from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    transaction_id: str
    amount: Decimal
    status: str
    transaction_type: str

    sender: str
    receiver: str

    sender_account_id: int
    receiver_account_id: int

    direction: str

    # risk_score: float | None = None
    # fraud_decision: str | None = None

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    limit: int
    offset: int
