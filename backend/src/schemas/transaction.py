from typing import Literal

from pydantic import BaseModel, Field


class Transaction(BaseModel):
    """PaySim-style input for the admin-only raw prediction endpoint."""

    type: Literal["CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]

    amount: float = Field(gt=0)

    oldbalanceOrg: float

    newbalanceOrig: float

    oldbalanceDest: float

    newbalanceDest: float

    step: int | None = Field(
        default=None,
        ge=1,
        le=743,
        description="Hours since start of the 30-day PaySim simulation. "
        "Defaults to the current hour of the month.",
    )
