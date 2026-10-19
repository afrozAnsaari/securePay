from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

import secrets

from src.databases.postgres.database import get_db

from src.databases.postgres.models import Merchant

router = APIRouter(tags=["Merchants"])


@router.post("/merchants")
def create_merchant(name: str, db: Session = Depends(get_db)):

    api_key = "sk_test" + secrets.token_hex(24)

    merchant = Merchant(name=name, api_key=api_key)

    db.add(merchant)

    db.commit()

    db.refresh(merchant)

    return {"merchant_id": merchant.id, "api_key": api_key}
