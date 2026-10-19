from fastapi import (
    Depends,
    Header,
    HTTPException,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from sqlalchemy.orm import Session


from src.databases.postgres.database import get_db
from src.databases.postgres.models import Merchant

security = HTTPBearer()


def verify_api_key(
    x_api_key: str = Header(None),
    db: Session = Depends(get_db),
) -> Merchant:

    if x_api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key",
        )
    merchant = db.query(Merchant).filter(Merchant.api_key == x_api_key).first()

    if merchant is None:
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key",
        )

    return merchant
