from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from src.schemas.pin import BalanceRequest
from src.databases.postgres.database import get_db

from src.databases.postgres.models import (
    User,
    UPIProfile,
)

from src.auth.verify_payment_pin import verify_upi_pin
from src.auth.verify_user import get_current_user

from src.config.rate_limits import RATE_LIMITS
from src.core.audit_events import AuditEvent
from src.exceptions.payments_exceptions import InvalidUPIPinError, invalid_pin_message
from src.security.security_audit_service import create_security_audit_log
from src.services.redis.rate_limit_service import check_rate_limit

from src.services.account.account_service import get_linked_account

router = APIRouter(tags=["Accounts"])


@router.post("/accounts/get-balance")
def get_balance(
    request: BalanceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    check_rate_limit(
        key=f"user:{user.id}:balance",
        limit=RATE_LIMITS["balance"]["limit"],
        window=RATE_LIMITS["balance"]["window"],
    )

    # --------------------------------------------
    # 1. Find selected UPI Profile
    # --------------------------------------------

    profile = (
        db.query(UPIProfile)
        .filter(
            UPIProfile.id == request.upi_profile_id,
            UPIProfile.user_id == user.id,
            UPIProfile.is_active == True,
        )
        .first()
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Selected UPI Profile not found.",
        )

    # --------------------------------------------
    # 2. Verify UPI PIN
    # --------------------------------------------

    try:
        verify_upi_pin(
            request.upi_pin,
            profile,
        )
    except InvalidUPIPinError as exc:
        create_security_audit_log(
            event_type=AuditEvent.UPI_PIN_FAILED,
            user_id=user.id,
            resource_type="UPIProfile",
            resource_id=str(profile.id),
            metadata={
                "reason": "INVALID_UPI_PIN",
                "action": "BALANCE_CHECK",
                "attempts_left": exc.attempts_left,
            },
        )
        raise HTTPException(
            status_code=403,
            detail=invalid_pin_message(exc.attempts_left),
        )

    # --------------------------------------------
    # 3. Get selected linked account
    # --------------------------------------------

    account = get_linked_account(
        db=db,
        user_id=user.id,
        account_id=request.account_id,
    )

    # --------------------------------------------
    # 4. Return balance
    # --------------------------------------------

    return {
        "account_id": account.id,
        "bank_name": account.bank_name,
        "account_type": account.account_type,
        "balance": account.balance,
    }
