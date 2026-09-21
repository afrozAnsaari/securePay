from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.auth.verify_user import get_current_user
from src.databases.database import get_db
from src.databases.models import User
from src.schemas.user_profile import UserProfileResponse

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
):
    return UserProfileResponse(
        first_name=current_user.customer.first_name,
        last_name=current_user.customer.last_name,
        mobile_no=current_user.mobile_no,
    )
