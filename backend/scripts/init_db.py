"""
Bring the database schema up to date by running the Alembic migrations.

Safe to run on every deploy: migrations that were already applied are
skipped, so it never deletes data. In Docker Compose it runs as the
one-off `migrate` service before the API starts.

Databases created before migrations existed (by the old create_all
version of this script) already have every table but no record of it.
For those, the script checks that the tables match the first migration
and marks them as being at that revision ("stamp") instead of trying to
create the tables again. Newer migrations then run as normal.

Usage (from backend/):
    DATABASE_URL="<neon connection string>" python scripts/init_db.py

Without DATABASE_URL on the command line, the value in backend/.env is used.
"""

import _bootstrap  # noqa: F401  (sets up imports)

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from src.databases.postgres.database import engine

BASELINE_REVISION = "b9e67580b69a"  # migrations/versions/..._initial_schema.py

BASELINE_TABLES = {
    "accounts",
    "audit_logs",
    "cards",
    "customers",
    "ledger_entries",
    "linked_bank_accounts",
    "merchants",
    "payment_idempotency",
    "payments",
    "refresh_tokens",
    "upi_profiles",
    "users",
}


def main() -> None:
    print(f"Target database: {_bootstrap.describe_target()}")

    alembic_cfg = Config(str(_bootstrap.BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(_bootstrap.BACKEND_DIR / "migrations"))

    tables = set(inspect(engine).get_table_names())

    if "alembic_version" not in tables and tables & BASELINE_TABLES:
        missing = sorted(BASELINE_TABLES - tables)
        if missing:
            raise SystemExit(
                "ERROR: this database has some SecurePay tables but not all of them "
                f"(missing: {', '.join(missing)}). Fix it by hand before migrating."
            )
        print("Existing schema found without migration history: marking it as the initial revision.")
        command.stamp(alembic_cfg, BASELINE_REVISION)

    command.upgrade(alembic_cfg, "head")
    print("OK: database schema is up to date.")


if __name__ == "__main__":
    main()
