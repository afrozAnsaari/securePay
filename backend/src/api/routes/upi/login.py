from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)


from src.services.token_service import create_user_refresh_token

from sqlalchemy.orm import Session

from src.databases.database import get_db

from src.databases.models import User

from src.schemas.auth import LoginRequest

from src.security.password import verify_password

from src.auth.jwt import create_access_token

router = APIRouter(tags=["Auth"])


@router.post(
    "/login",
    responses={
        401: {"description": "Incorrect mobile number or password"},
    },
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(User.mobile_no == credentials.mobile_no).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid mobile or passwords. Please try again",
        )

    valid_password = verify_password(
        credentials.password,
        user.password_hash,
    )

    if not valid_password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect mobile number or password",
        )

    access_token = create_access_token(
        {
            "user_id": user.id,
        }
    )

    refresh_token = create_user_refresh_token(
        db=db,
        user_id=user.id,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
