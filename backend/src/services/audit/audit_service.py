from typing import Any

from sqlalchemy.orm import Session

from src.databases.audit_log import AuditLog


def create_audit_log(
    db: Session,
    event_type: str,
    user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:

    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata,
    )

    db.add(audit_log)
    db.flush()

    return audit_log
