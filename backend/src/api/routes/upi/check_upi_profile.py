from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.auth.verify_user import get_current_user

from src.databases.database import get_db

from src.databases.models import User, UPIProfile


from src.schemas.upi import UPIProfileRespnse

router = APIRouter(tags=["UPI"], prefix="/upi")


@router.get("/get-profile", response_model=UPIProfileRespnse)
def get_upi_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    profile: UPIProfile = (
        db.query(UPIProfile)
        .filter(
            UPIProfile.user_id == current_user.id,
            UPIProfile.is_active == True,
        )
        .first()
    )

    if profile is None:

        return UPIProfileRespnse(exists=False, upi_pin_exists=False)

    return UPIProfileRespnse(
        exists=True,
        upi_id=profile.upi_id,
        upi_pin_exists=profile.upi_pin_hash is not None,
    )
