from decimal import Decimal
import re

from pydantic import BaseModel, field_validator, Field

from src.utils.enums.BankName import BankName
from src.utils.enums.AccountType import AccountType

MOBILE_NO_REGEX = re.compile(r"^\d{10}$")


class AccountCreate(BaseModel):
    customer_id: int
    bank_name: BankName
    account_type: AccountType
    initial_balance: Decimal = Field(gt=Decimal("0.00"))
    mobile_no: str

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile_no(cls, value: str):
        if not MOBILE_NO_REGEX.fullmatch(value):
            raise ValueError("Phone number is not valid")
        return value


class LinkedAccountResponse(BaseModel):
    account_id: int
    bank_name: str
    masked_account_number: str
    is_primary: bool


class LinkedAccountsResponse(BaseModel):
    accounts: list[LinkedAccountResponse]
