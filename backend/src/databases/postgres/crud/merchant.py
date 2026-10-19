import secrets
from sqlalchemy.orm import Session

from src.databases.postgres.models.merchant import Merchant


def create_merchant(db: Session, merchant_data: dict):
    api_key = "sk_test" + secrets.token_hex(32)
    merchant = Merchant(name=merchant_data["name"], api_key=api_key)

    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    return merchant
