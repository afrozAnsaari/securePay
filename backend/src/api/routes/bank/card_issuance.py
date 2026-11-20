from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.auth.verify_admin import require_admin

from src.schemas.card import CardCreate

from src.databases.postgres.database import get_db

from src.databases.postgres.crud import create_card

router = APIRouter(
    tags=["Issue Cards (admin)"],
    dependencies=[Depends(require_admin)],
)


@router.post("/cards/issuance")
def issue_card(card: CardCreate, db: Session = Depends(get_db)):

    return create_card(card_data=card, db=db)
