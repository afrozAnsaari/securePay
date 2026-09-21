import logging

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.auth.verify_user import get_current_user
from src.databases.database import get_db
from src.databases.models import User
from src.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/test",
    tags=["Test"],
)


@router.post("/audit")
def test_audit_log(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logger.info(
        "Testing audit logging user_id=%s",
        current_user.id,
    )

    audit_log = create_audit_log(
        db=db,
        event_type="TEST_EVENT",
        user_id=current_user.id,
        resource_type="Test",
        resource_id="test-001",
        metadata={
            "source": "audit_test",
        },
    )

    db.commit()

    return {
        "message": "Audit log created",
        "audit_log_id": audit_log.id,
    }


@router.post("/audit-rollback")
def test_audit_rollback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        create_audit_log(
            db=db,
            event_type="ROLLBACK_TEST",
            user_id=current_user.id,
            resource_type="Test",
            resource_id="rollback-test",
            metadata={
                "source": "rollback_test",
            },
        )

        # Force an error after the audit log has been flushed.
        raise RuntimeError("Intentional rollback test")

    except Exception:
        db.rollback()

        logger.info(
            "Audit rollback test completed user_id=%s",
            current_user.id,
        )

        return {
            "message": "Rollback executed successfully",
        }
