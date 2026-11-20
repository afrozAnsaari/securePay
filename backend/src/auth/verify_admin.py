import secrets

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.config import settings

admin_key_header = APIKeyHeader(
    name="X-Admin-Key",
    auto_error=False,
    description="Owner-only key for the bank simulator routes (ADMIN_API_KEY in .env).",
)


def require_admin(api_key: str | None = Security(admin_key_header)) -> None:
    """
    Protects the "bank side" of the simulation (creating customers, bank
    accounts and cards, raw model predictions).

    The frontend never has this key, so app users cannot reach these routes.
    """

    if not api_key:
        raise HTTPException(status_code=401, detail="Admin key required.")

    # Constant-time comparison so the key can't be guessed via response timing.
    if not secrets.compare_digest(api_key, settings.ADMIN_API_KEY):
        raise HTTPException(status_code=403, detail="Invalid admin key.")
