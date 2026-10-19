from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.databases.postgres.database import get_db

from src.auth.verify_user import get_current_user


from src.schemas.pin import SetPinRequest

from src.security.password import hash_password

from src.databases.postgres.models import User

router = APIRouter(tags=["set-pin"])


@router.post("/set-pin")
def set_pin(
    data: SetPinRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if user.payment_pin_hash is not None:
        raise HTTPException(
            status_code=409,
            detail="UPI PIN already exists",
        )

    user.payment_pin_hash = hash_password(data.pin)

    db.commit()

    return {
        "message": "PIN created successfully",
    }
