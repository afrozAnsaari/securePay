import re

from pydantic import BaseModel, field_validator

UPI_ID_REGEX = re.compile(r"[a-z][a-z0-9._]*")

UPI_ID_SUFFIX = "@securepay"


class UPIProfileCreate(BaseModel):

    upi_id: str

    upi_pin: str

    @field_validator("upi_id")
    @classmethod
    def validate_upi_id(cls, value: str):

        value = value.strip().lower()

        # If user enters the complete UPI ID,
        # remove the UPI_ID_SUFFIX part for validation.
        if value.endswith(UPI_ID_SUFFIX):
            username = value.removesuffix(UPI_ID_SUFFIX)
        else:
            # User only entered the username.
            username = value

        if not username:
            raise ValueError("UPI ID cannot be empty.")

        # Same 4-16 limit the payment code uses to look up a receiver
        # (src/services/payment/input_validator.py), so every UPI ID that
        # can be created can also receive money.
        if len(username) < 4:
            raise ValueError("UPI ID must be at least 4 characters.")

        if len(username) > 16:
            raise ValueError("UPI ID cannot be more than 16 characters.")

        # Must start with a letter.
        if not username[0].isalpha():
            raise ValueError("UPI ID must start with a letter.")

        # Only letters, numbers, . and _
        if not re.fullmatch(UPI_ID_REGEX, username):
            raise ValueError("UPI ID can contain only letters, numbers, '.' and '_'")

        # Don't allow consecutive special characters.
        if re.search(r"[._]{2,}", username):
            raise ValueError("UPI ID cannot contain consecutive '.' or '_'")
        # Don't allow . or _ at the end.
        if username[-1] in "._":
            raise ValueError("UPI ID cannot end with '.' or '_'")

        # Add our UPI handle automatically.
        return username + UPI_ID_SUFFIX

    @field_validator("upi_pin")
    @classmethod
    def validate_upi_pin(cls, value: str):

        if not value.isdigit() or not (4 <= len(value) <= 6):
            raise ValueError("Invalid PIN")
        return value
