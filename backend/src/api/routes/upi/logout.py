from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi import Depends

from src.databases.database import get_db
from src.databases.refresh_token import RefreshToken
from src.schemas.auth import LogoutRequest
from src.security.hash_utils import sha256_hash

from src.core.audit_events import AuditEvent
from src.services.audit_service import create_audit_log

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/logout",
    responses={
        401: {
            "description": "Invalid or already revoked refresh token",
        },
    },
)
def logout(
    request: LogoutRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    token_hash = sha256_hash(request.refresh_token)

    stored_token = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
        )
        .first()
    )

    if stored_token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token.",
        )

    if stored_token.revoked:
        raise HTTPException(
            status_code=401,
            detail="Refresh token already revoked.",
        )

    try:
        stored_token.revoked = True

        create_audit_log(
            db=db,
            event_type=AuditEvent.USER_LOGOUT,
            user_id=stored_token.user_id,
            resource_type="User",
            resource_id=str(stored_token.user_id),
            ip_address=(http_request.client.host if http_request.client else None),
            user_agent=http_request.headers.get("user-agent"),
            metadata={
                "method": "refresh_token",
            },
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Logged out successfully.",
    }
