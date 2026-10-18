from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from src.schemas.pin import BalanceRequest
from src.databases.database import get_db

from src.databases.models import (
    User,
    UPIProfile,
)

from src.auth.verify_payment_pin import verify_upi_pin
from src.auth.verify_user import get_current_user

from src.services.account.account_service import get_linked_account

router = APIRouter(tags=["Accounts"])


@router.post("/accounts/get-balance")
def get_balance(
    request: BalanceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

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

    verify_upi_pin(
        request.upi_pin,
        profile,
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
