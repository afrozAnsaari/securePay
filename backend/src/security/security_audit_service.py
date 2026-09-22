from typing import Any

from src.databases.database import SessionLocal
from src.core.audit_events import AuditEvent
from src.services.audit_service import create_audit_log


def create_security_audit_log(
    event_type: AuditEvent,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    db = SessionLocal()

    try:
        create_audit_log(
            db=db,
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
