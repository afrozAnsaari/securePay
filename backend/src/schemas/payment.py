from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_validator


class PaymentCreate(BaseModel):

    model_config = ConfigDict(frozen=True)

    receiver: str = Field(
        ...,
        description="Receiver mobile number or UPI ID",
    )

    sender_upi_profile_id: int = Field(
        ...,
        description="UPI Profile of the sender used to initiate the payment",
    )

    sender_account_id: int = Field(
        ...,
        description="Linked Bank Account used to fund payment",
    )

    amount: Decimal = Field(
        ...,
        description="Amount to be transferred",
        gt=Decimal("0.00"),
    )

    upi_pin: str = Field(
        ...,
    )

    @field_validator("upi_pin")
    @classmethod
    def validate_upi_pin(cls, value: str):

        if not value.isdigit() or not (4 <= len(value) <= 6):
            raise ValueError("UPI PIN must be 4-6 digits.")

        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal):

        if value <= 0:
            raise ValueError("Amount should be greater than zero")
        return value.quantize(Decimal("0.01"))


class PaymentResponse(BaseModel):
    transaction_id: str
    amount: Decimal
    status: str
    receiver: str
    transaction_type: str
    created_at: datetime
    message: str

    model_config = ConfigDict(from_attributes=True)
