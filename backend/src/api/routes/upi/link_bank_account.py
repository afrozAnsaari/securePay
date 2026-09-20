from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.auth.verify_user import get_current_user

from src.databases.database import get_db

from src.databases.crud import link_bank_acc

from src.databases.models import User

from src.schemas.link_bank_request import LinkBankRequest


from src.services.rate_limit_service import check_rate_limit

from src.config.rate_limits import RATE_LIMITS

router = APIRouter(
    prefix="/upi",
    tags=["UPI"],
)


@router.post("/link-bank")
def link_bank(
    data: LinkBankRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    check_rate_limit(
        key=f"lba:user:{current_user.id}",
        limit=RATE_LIMITS["lba"]["limit"],
        window=RATE_LIMITS["lba"]["window"],
    )

    return link_bank_acc(data, db, current_user)
