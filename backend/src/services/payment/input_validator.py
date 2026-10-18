import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.models import UPIProfile, User

# --------------------------------------------------
# Phone number
# --------------------------------------------------

PHONE_NUMBER_REGEX = re.compile(r"^[6-9]\d{9}$")


# --------------------------------------------------
# SecurePay UPI username
#
# Rules:
# - Must start with a letter
# - Maximum 16 characters
# - Numbers allowed after first character
# - "." and "_" allowed
# - No spaces
# - "." and "_" cannot be first
# - "." and "_" cannot be last
# - No consecutive special characters
# --------------------------------------------------


# Enforces a total length of 6 to 16 characters
import re

# Enforces all rules including a total length of 6 to 16 characters
UPI_USERNAME_REGEX = re.compile(
    r"^(?=.{4,16}$)[a-z](?:[a-z0-9]|[_.(?!_.)](?![_.]))*[a-z0-9]$", re.IGNORECASE
)


def resolve_receiver(
    db: Session,
    receiver: str,
) -> UPIProfile:

    receiver = receiver.strip().lower()

    if not receiver:

        raise HTTPException(
            status_code=400,
            detail="Receiver cannot be empty.",
        )

    # ==================================================
    # PHONE NUMBER
    # ==================================================

    if PHONE_NUMBER_REGEX.fullmatch(receiver):

        user = (
            db.query(User)
            .filter(
                User.mobile_no == receiver,
            )
            .first()
        )

        if user is None:

            raise HTTPException(
                status_code=404,
                detail="User not found.",
            )

        profile = (
            db.query(UPIProfile)
            .filter(
                UPIProfile.user_id == user.id,
                UPIProfile.is_active == True,
            )
            .first()
        )

        if profile is None:

            raise HTTPException(
                status_code=404,
                detail="Receiver UPI profile not found.",
            )

        return profile

    # ==================================================
    # UPI ID
    # ==================================================

    # If the user supplied @securepay, remove it temporarily
    # so that we validate only the username portion.
    if receiver.endswith("@securepay"):

        username = receiver.removesuffix("@securepay")

    else:

        # Reject other @handles.
        if "@" in receiver:

            raise HTTPException(
                status_code=400,
                detail="Invalid UPI ID. Use the @securepay handle.",
            )

        username = receiver

    # --------------------------------------------------
    # Username length
    # --------------------------------------------------

    if not username:

        raise HTTPException(
            status_code=400,
            detail="UPI ID cannot be empty.",
        )

    if len(username) > 16:

        raise HTTPException(
            status_code=400,
            detail="UPI ID cannot be more than 16 characters.",
        )

    # --------------------------------------------------
    # Must start with a letter
    # --------------------------------------------------

    if not username[0].isalpha():

        raise HTTPException(
            status_code=400,
            detail="UPI ID must start with a letter.",
        )

    # --------------------------------------------------
    # Allowed characters
    # --------------------------------------------------

    if not UPI_USERNAME_REGEX.fullmatch(username):

        raise HTTPException(
            status_code=400,
            detail=("UPI ID can contain only letters, numbers, " "'.' and '_'."),
        )

    # --------------------------------------------------
    # No consecutive special characters
    # --------------------------------------------------

    if re.search(r"[._]{2,}", username):

        raise HTTPException(
            status_code=400,
            detail=("UPI ID cannot contain consecutive " "'.' or '_'."),
        )

    # --------------------------------------------------
    # Cannot end with . or _
    # --------------------------------------------------

    if username[-1] in "._":

        raise HTTPException(
            status_code=400,
            detail="UPI ID cannot end with '.' or '_'.",
        )

    # --------------------------------------------------
    # Construct canonical UPI ID
    # --------------------------------------------------

    upi_id = f"{username}@securepay"

    # ==================================================
    # FIND PROFILE
    # ==================================================

    profile = (
        db.query(UPIProfile)
        .filter(
            UPIProfile.upi_id == upi_id,
            UPIProfile.is_active == True,
        )
        .first()
    )

    if profile is None:

        raise HTTPException(
            status_code=404,
            detail="Receiver UPI profile not found.",
        )

    return profile
