from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, JSON

from src.databases.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
        index=True,
    )

    resource_type = Column(
        String(50),
        nullable=True,
    )

    resource_id = Column(
        String(100),
        nullable=True,
    )

    ip_address = Column(
        String(45),
        nullable=True,
    )

    user_agent = Column(
        String(500),
        nullable=True,
    )

    metadata_json = Column(
        JSON,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
