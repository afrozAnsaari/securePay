"""
Central place for every secret and environment-specific setting.

Values come from environment variables (loaded from backend/.env).
Nothing secret is hard-coded: if a required value is missing the app
refuses to start and says which one.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        _missing.append(name)
    return value


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


_missing: list[str] = []

# --- Databases -------------------------------------------------------------
DATABASE_URL = _required("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# --- Auth ------------------------------------------------------------------
JWT_SECRET_KEY = _required("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _int("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
REFRESH_TOKEN_EXPIRE_DAYS = _int("REFRESH_TOKEN_EXPIRE_DAYS", 7)

# --- Encryption ------------------------------------------------------------
ENCRYPTION_KEY = _required("ENCRYPTION_KEY")

# --- Admin (bank simulator) ------------------------------------------------
# The /bank/*, /cards/issuance and /admin/* routes are the "bank side" of the
# simulation. They are never called by the frontend; only the owner can use
# them by sending this key in the X-Admin-Key header.
ENABLE_ADMIN_ROUTES = _bool("ENABLE_ADMIN_ROUTES", True)
ADMIN_API_KEY = _required("ADMIN_API_KEY") if ENABLE_ADMIN_ROUTES else ""

# --- HTTP ------------------------------------------------------------------
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

if _missing:
    raise RuntimeError(
        "Missing required environment variables: "
        + ", ".join(_missing)
        + ". Copy backend/.env.example to backend/.env and fill them in."
    )

if ENABLE_ADMIN_ROUTES and len(ADMIN_API_KEY) < 32:
    raise RuntimeError(
        "ADMIN_API_KEY must be at least 32 characters. Generate one with: "
        'python -c "import secrets; print(secrets.token_urlsafe(32))"'
    )

if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must be at least 32 characters. Generate one with: "
        'python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )
