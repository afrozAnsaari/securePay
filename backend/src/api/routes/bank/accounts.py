from fastapi import (
    APIRouter,
    Depends,
)


from sqlalchemy.orm import Session

from src.databases.postgres.database import get_db

from src.schemas.account import AccountCreate

from src.databases.postgres.crud import create_account

router = APIRouter(
    prefix="/bank",
    tags=["Bank Accounts"],
)


@router.post("/accounts")
def open_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
):

    created_account = create_account(db, account)

    return {
        "account_id": created_account.id,
        "account_number": created_account.account_number,
        "bank_name": created_account.bank_name,
        "ifsc_code": created_account.ifsc_code,
        "balance": created_account.balance,
        "status": created_account.status,
    }
