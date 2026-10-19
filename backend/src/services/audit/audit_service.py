from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from src.databases.postgres.models import AuditLog


def _sanitize_metadata(val: Any) -> Any:
    if isinstance(val, Decimal):
        return str(val)
    elif isinstance(val, dict):
        return {k: _sanitize_metadata(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [_sanitize_metadata(item) for item in val]
    return val


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

    sanitized_metadata = _sanitize_metadata(metadata) if metadata else None

    audit_log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=sanitized_metadata,
    )

    db.add(audit_log)
    db.flush()

    return audit_log
