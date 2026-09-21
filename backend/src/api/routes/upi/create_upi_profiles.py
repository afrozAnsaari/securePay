from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session


from src.databases.crud import create_upi_profile
from src.databases.database import get_db

from src.auth.verify_user import get_current_user

from src.schemas.upi_profile import UPIProfileCreate

from src.databases.models import User

router = APIRouter(tags=["UPI"], prefix="/upi")


@router.post("/create-profile")
def create_profile(
    profile: UPIProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return create_upi_profile(
        db=db,
        profile_data=profile,
        current_user=current_user,
    )
