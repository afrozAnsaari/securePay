from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.postgres.models.account import Account
from src.databases.postgres.models.customer import Customer
from src.databases.postgres.models.user import User
from src.schemas.account import AccountCreate
from src.schemas.discover_acccount_req import DiscoverAccountsRequest
from src.utils.bank_utils import generate_account_number, get_ifsc_code


def get_account_balance(db: Session, account_id: int):
    account = db.query(Account).filter(Account.id == account_id).first()
    return account


def create_account(db: Session, account_data: AccountCreate) -> Account:
    customer = (
        db.query(Customer).filter(Customer.id == account_data.customer_id).first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="Customer KYC incomplete",
        )

    account = Account(
        customer_id=customer.id,
        account_number=generate_account_number(),
        bank_name=account_data.bank_name,
        ifsc_code=get_ifsc_code(account_data.bank_name),
        account_type=account_data.account_type,
        balance=account_data.initial_balance,
        status="ACTIVE",
        mobile_no=account_data.mobile_no,
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account


def fetch_accounts(db: Session, request: DiscoverAccountsRequest):
    user = db.query(User).filter(User.id == request.user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    customer = (
        db.query(Customer).filter(Customer.mobile_no == request.mobile_no).first()
    )

    if customer is None:
        raise HTTPException(
            status_code=404,
            detail="No bank customer found with this mobile number",
        )

    accounts = db.query(Account).filter(Account.customer_id == customer.id).all()

    if not accounts:
        raise HTTPException(
            status_code=404,
            detail="No accounts found",
        )

    return [
        {
            "account_id": account.id,
            "bank_name": account.bank_name,
            "account_type": account.account_type,
        }
        for account in accounts
    ]
