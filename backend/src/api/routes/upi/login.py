from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from src.services.rate_limit_service import check_rate_limit
from src.config.rate_limits import RATE_LIMITS


from src.services.token_service import create_user_refresh_token

from sqlalchemy.orm import Session

from src.databases.database import get_db

from src.databases.models import User

from src.schemas.auth import LoginRequest

from src.security.password import verify_password

from src.auth.jwt import create_access_token

from src.core.audit_events import AuditEvent

from src.services.audit_service import create_audit_log

router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post(
    "/login",
    responses={
        401: {"description": "Incorrect mobile number or password"},
    },
)
def login(
    credentials: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"

    check_rate_limit(
        key=f"login:ip:{client_ip}",
        limit=RATE_LIMITS["login"]["limit"],
        window=RATE_LIMITS["login"]["window"],
    )

    user = db.query(User).filter(User.mobile_no == credentials.mobile_no).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid mobile or password.",
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

    try:
        access_token = create_access_token({"user_id": user.id})

        refresh_token = create_user_refresh_token(
            db=db,
            user_id=user.id,
        )

        create_audit_log(
            db=db,
            event_type=AuditEvent.USER_LOGIN,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            ip_address=client_ip,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "method": "password",
            },
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
