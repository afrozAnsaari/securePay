from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.models import (
    LinkedBankAccount,
    Account,
)


def get_linked_accounts(
    db: Session,
    user_id: int,
) -> list[LinkedBankAccount]:

    linked_accounts = (
        db.query(LinkedBankAccount)
        .filter(
            LinkedBankAccount.user_id == user_id,
        )
        .all()
    )

    return linked_accounts


def get_linked_account(
    db: Session,
    user_id: int,
    account_id: int,
) -> Account:

    linked_account = (
        db.query(LinkedBankAccount)
        .filter(
            LinkedBankAccount.user_id == user_id,
            LinkedBankAccount.account_id == account_id,
        )
        .first()
    )

    if linked_account is None:
        raise HTTPException(
            status_code=404,
            detail="Bank account is not linked to this user.",
        )

    return linked_account.account
