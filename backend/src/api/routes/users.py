from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.databases.postgres.database import get_db

from src.schemas.user import UserCreate

from src.databases.postgres.crud import create_user

router = APIRouter(tags=["Users"])


@router.post("/users/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    created = create_user(
        db=db,
        user_data=user,
    )

    return {
        "message": created["message"],
        "user_id": created["user_id"],
        "name": created["name"],
        "mobile_no": created["mobile_no"],
        "email": created["email"],
    }
