from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.databases.postgres.crud import fetch_accounts

from src.databases.postgres.database import get_db

from src.schemas.discover_acccount_req import DiscoverAccountsRequest

router = APIRouter(tags=["Fetch Accounts"])


@router.post("/discover-accounts")
def discover(request: DiscoverAccountsRequest, db: Session = Depends(get_db)):

    return fetch_accounts(db, request)
