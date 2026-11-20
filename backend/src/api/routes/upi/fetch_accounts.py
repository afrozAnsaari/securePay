from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.auth.verify_user import get_current_user
from src.databases.postgres.crud import fetch_accounts
from src.databases.postgres.database import get_db
from src.databases.postgres.models import User

router = APIRouter(tags=["Fetch Accounts"])


@router.post("/discover-accounts")
def discover(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Only accounts registered to the logged-in user's own mobile number
    # are returned, so nobody can look up someone else's bank accounts.
    return fetch_accounts(db, current_user)
