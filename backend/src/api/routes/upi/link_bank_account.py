from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from src.schemas.link_bank_request import LinkBankRequest

from src.core.audit_events import AuditEvent

from src.services.audit_service import create_audit_log

from src.auth.verify_user import get_current_user

from src.databases.database import get_db

from src.databases.crud import link_bank_acc

from src.databases.models import User


from src.services.rate_limit_service import check_rate_limit

from src.config.rate_limits import RATE_LIMITS

router = APIRouter(
    prefix="/upi",
    tags=["UPI"],
)


@router.post("/link-bank")
def link_bank(
    data: LinkBankRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_rate_limit(
        key=f"lba:user:{current_user.id}",
        limit=RATE_LIMITS["lba"]["limit"],
        window=RATE_LIMITS["lba"]["window"],
    )

    try:
        result = link_bank_acc(
            data,
            db,
            current_user,
        )

        create_audit_log(
            db=db,
            event_type=AuditEvent.BANK_ACCOUNT_LINKED,
            user_id=current_user.id,
            resource_type="LinkedBankAccount",
            resource_id=str(result["linked_account_id"]),
            ip_address=(request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent"),
            metadata={
                "bank_name": result["bank_name"].value,
                "account_type": result["account_type"].value,
                "is_primary": result["is_primary"],
            },
        )

        db.commit()

        return result

    except Exception:
        db.rollback()
        raise
