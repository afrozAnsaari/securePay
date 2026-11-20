"""Lets the scripts import `src.` and shows which database they will touch."""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))


def describe_target() -> str:
    from sqlalchemy.engine import make_url

    from src.config import settings

    url = make_url(settings.DATABASE_URL)
    return f"{url.host}:{url.port or 5432}/{url.database}"
