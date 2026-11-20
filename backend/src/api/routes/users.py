from fastapi import APIRouter, Depends, Request

from sqlalchemy.orm import Session

from src.config.rate_limits import RATE_LIMITS
from src.databases.postgres.database import get_db
from src.schemas.user import UserCreate
from src.databases.postgres.crud import create_user
from src.services.redis.rate_limit_service import check_rate_limit

router = APIRouter(tags=["Users"])


@router.post("/users/register")
def register_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"

    check_rate_limit(
        key=f"register:ip:{client_ip}",
        limit=RATE_LIMITS["register"]["limit"],
        window=RATE_LIMITS["register"]["window"],
    )

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
