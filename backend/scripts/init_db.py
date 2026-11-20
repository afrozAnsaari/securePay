"""
Create every SecurePay table from the current SQLAlchemy models.

Safe to run more than once: existing tables are left untouched, only
missing ones are created. It never deletes data.

Usage (from backend/):
    DATABASE_URL="<neon connection string>" python scripts/init_db.py

Without DATABASE_URL on the command line, the value in backend/.env is used.
"""

import _bootstrap  # noqa: F401  (sets up imports)

from sqlalchemy import inspect

from src.databases.postgres.database import engine
from src.databases.postgres.models import Base


def main() -> None:
    print(f"Target database: {_bootstrap.describe_target()}")

    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(engine)
    after = set(inspect(engine).get_table_names())

    created = sorted(after - before)
    expected = sorted(Base.metadata.tables)

    print(f"Created {len(created)} table(s): {', '.join(created) or 'none (already existed)'}")

    missing = [t for t in expected if t not in after]
    if missing:
        raise SystemExit(f"ERROR: tables still missing: {', '.join(missing)}")

    print(f"OK: all {len(expected)} tables present.")


if __name__ == "__main__":
    main()
