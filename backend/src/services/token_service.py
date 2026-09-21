from datetime import datetime, timedelta, timezone


from fastapi import HTTPException

from sqlalchemy.orm import Session

from src.databases.refresh_token import RefreshToken

from src.auth.jwt import create_refresh_token, REFRESH_TOKEN_EXPIRY_IN_DAYS

from src.security.hash_utils import sha256_hash


def create_user_refresh_token(
    db: Session,
    user_id: int,
):

    raw_token = create_refresh_token()

    token_hash = sha256_hash(raw_token)

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=REFRESH_TOKEN_EXPIRY_IN_DAYS
    )

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(refresh_token)

    db.flush()

    return raw_token
