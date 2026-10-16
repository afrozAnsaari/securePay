import re

from datetime import date

from pydantic import BaseModel, EmailStr, field_validator

PAN_REGEX = re.compile(r"^[A-Z]{5}\d{4}[A-Z]$")


class CustomerCreate(BaseModel):

    full_name: str

    dob: date

    mobile_no: str

    email: EmailStr

    aadhar_no: str

    pan_no: str

    address: str

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile_no(cls, value: str):

        if not value.isdigit() and len(value) == 10:
            raise ValueError("Please enter a valid mobile number")
        return value

    @field_validator("pan_no")
    @classmethod
    def validate_pan_no(cls, value: str):

        if not PAN_REGEX.fullmatch(value):
            raise ValueError("The pan card is invalid")

        return value

    @field_validator("aadhar_no")
    @classmethod
    def validate_aadhar_no(cls, value: str):
        if not value.isdigit() and len(value) == 12:
            raise ValueError("The aadhaar number is invalid")
        return value
