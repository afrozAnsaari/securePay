from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.databases.models import User

from src.databases.database import get_db
from src.auth.verify_user import get_current_user

from src.schemas.account import LinkedAccountsResponse
from src.services.account_service import get_linked_accounts

router = APIRouter(tags=["UPI"], prefix="/upi")


@router.get(
    "/accounts/linked",
    response_model=LinkedAccountsResponse,
)
def get_user_linked_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    linked_accounts = get_linked_accounts(
        db=db,
        user_id=current_user.id,
    )

    accounts = []

    for linked_account in linked_accounts:

        account = linked_account.account

        account_number = account.account_number

        masked_account_number = "*" * (len(account_number) - 4) + account_number[-4:]

        accounts.append(
            {
                "account_id": account.id,
                "bank_name": account.bank_name.value,
                "masked_account_number": masked_account_number,
                "is_primary": linked_account.is_primary,
            }
        )

    return {
        "accounts": accounts,
    }
