from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.postgres.models.account import Account
from src.databases.postgres.models.card import Card
from src.databases.postgres.models.customer import Customer
from src.databases.postgres.models.linked_bank_account import LinkedBankAccount
from src.databases.postgres.models.upi_profile import UPIProfile
from src.databases.postgres.models.user import User
from src.schemas.link_bank_request import LinkBankRequest
from src.schemas.upi_profile import UPIProfileCreate
from src.security.hash_utils import sha256_hash
from src.security.password import hash_password, verify_password


def create_upi_profile(
    db: Session,
    profile_data: UPIProfileCreate,
    current_user: User,
):
    existing = (
        db.query(UPIProfile).filter(UPIProfile.upi_id == profile_data.upi_id).first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="UPI ID already exists. Please choose another UPI ID",
        )

    profile: UPIProfile = UPIProfile(
        user_id=current_user.id,
        upi_id=profile_data.upi_id,
        upi_pin_hash=hash_password(profile_data.upi_pin),
        is_active=True,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return {
        "message": "UPI Profile created successfully",
        "profile_id": profile.id,
        "upi_id": profile.upi_id,
    }


def link_bank_acc(
    data: LinkBankRequest,
    db: Session,
    current_user: User,
):
    profile = (
        db.query(UPIProfile)
        .filter(
            UPIProfile.user_id == current_user.id,
            UPIProfile.is_active == True,
        )
        .first()
    )

    if profile is None:
        raise HTTPException(status_code=404, detail="Create a UPI Profile first")

    card_no_hash = sha256_hash(data.card_number)

    card = db.query(Card).filter(Card.card_number_hash == card_no_hash).first()

    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.expiry_month != data.expiry_month or card.expiry_year != data.expiry_year:
        raise HTTPException(status_code=400, detail="Invalid card details")

    if not verify_password(data.card_pin, card.card_pin_hash):
        raise HTTPException(status_code=401, detail="Incorrent pin")

    account = db.query(Account).filter(Account.id == card.account_id).first()

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    if account.bank_name != data.bank_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid Card Details",
        )

    customer: Customer = (
        db.query(Customer).filter(Customer.id == account.customer_id).first()
    )

    if customer is None:
        raise HTTPException(status_code=404, detail="Account cannot be linked")

    if not customer.kyc_verified:
        raise HTTPException(status_code=409, detail="Your account cannot be linked")

    if customer.mobile_no != current_user.mobile_no:
        raise HTTPException(
            status_code=403, detail="This bank account does not belong to the user."
        )

    existing: LinkedBankAccount = (
        db.query(LinkedBankAccount)
        .filter(
            LinkedBankAccount.user_id == current_user.id,
            LinkedBankAccount.account_id == account.id,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Account already linked.")

    is_primary: bool = (
        db.query(LinkedBankAccount)
        .filter(LinkedBankAccount.user_id == current_user.id)
        .first()
    ) is None

    linked_account = LinkedBankAccount(
        user_id=current_user.id,
        account_id=account.id,
        is_primary=is_primary,
    )

    db.add(linked_account)
    db.flush()
    db.refresh(linked_account)

    return {
        "message": "Bank account linked successfully",
        "linked_account_id": linked_account.id,
        "bank_name": account.bank_name,
        "account_type": account.account_type,
        "is_primary": linked_account.is_primary,
    }
