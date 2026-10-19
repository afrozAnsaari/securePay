from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.postgres.models.user import User
from src.schemas.user import UserCreate
from src.security.password import hash_password


def create_user(db: Session, user_data: UserCreate):
    existing = db.query(User).filter(User.mobile_no == user_data.mobile_no).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Mobile number already registered",
        )

    existing_email = db.query(User).filter(User.email == user_data.email).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already registered. Please try to login",
        )

    user = User(
        name=user_data.name,
        mobile_no=user_data.mobile_no,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Your account has been registered sucessfully",
        "user_id": user.id,
        "name": user.name,
        "mobile_no": user.mobile_no,
        "email": user.email,
    }
