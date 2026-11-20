from fastapi import HTTPException

from src.security.password import verify_password
from src.exceptions.payments_exceptions import InvalidUPIPinError
from src.databases.postgres.models import UPIProfile, User
from src.services.redis.pin_lockout_service import (
    MAX_PIN_ATTEMPTS,
    clear_failures,
    ensure_not_locked,
    record_failure,
)


def verify_upi_pin(
    entered_pin: str,
    profile: UPIProfile,
):
    if profile.upi_pin_hash is None:
        raise HTTPException(
            status_code=403,
            detail="UPI PIN not set",
        )

    # Refuse before checking the PIN, so a locked profile can't be guessed.
    ensure_not_locked(profile.id)

    if not verify_password(
        entered_pin,
        profile.upi_pin_hash,
    ):
        failures = record_failure(profile.id)
        raise InvalidUPIPinError(attempts_left=max(MAX_PIN_ATTEMPTS - failures, 0))

    clear_failures(profile.id)


def verify_login_pin(
    entered_pin: str,
    user: User,
):

    if user.payment_pin_hash is None:
        raise HTTPException(
            status_code=403,
            detail="Payment PIN not set",
        )

    if not verify_password(entered_pin, user.payment_pin_hash):
        raise HTTPException(
            status_code=403,
            detail="Invalid Payment PIN",
        )
