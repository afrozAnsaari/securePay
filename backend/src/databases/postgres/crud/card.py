from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.postgres.models.account import Account
from src.databases.postgres.models.card import Card
from src.schemas.card import CardCreate
from src.security.encryption import encrypt_data
from src.security.hash_utils import sha256_hash
from src.security.password import hash_password
from src.utils.card_generator import generate_card_number, generate_expiry
from src.utils.enums.CardStatus import CardStatus


def create_card(card_data: CardCreate, db: Session):
    account = db.query(Account).filter(Account.id == card_data.account_id).first()

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Account not found",
        )

    card_no = generate_card_number(
        bank_name=account.bank_name.value,
        network=card_data.network.value,
        account_id=account.id,
    )

    existing_card = (
        db.query(Card)
        .filter(
            Card.account_id == account.id,
            Card.network == card_data.network,
            Card.status == CardStatus.ACTIVE,
        )
        .first()
    )

    if existing_card:
        raise HTTPException(
            status_code=409,
            detail="You already have a active debit card under this account.",
        )

    card_number_hash = sha256_hash(card_no)
    encrypted_card_no = encrypt_data(card_no)
    expiry_month, expiry_year = generate_expiry()
    card_pin_hash = hash_password(card_data.card_pin)

    card = Card(
        account_id=account.id,
        card_number_encrypted=encrypted_card_no,
        last4=card_no[-4:],
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        network=card_data.network,
        card_number_hash=card_number_hash,
        card_pin_hash=card_pin_hash,
    )

    db.add(card)
    db.commit()
    db.refresh(card)

    return {
        "card_id": card.id,
        "card_number": card_no,
        "expiry_month": expiry_month,
        "expiry_year": expiry_year,
        "network": card.network,
    }
