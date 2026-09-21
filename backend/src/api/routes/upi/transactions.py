from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from src.auth.verify_user import get_current_user
from src.databases.database import get_db

from src.databases.models import (
    User,
    Payment,
    UPIProfile,
)

from src.schemas.transaction_history import (
    TransactionResponse,
    TransactionListResponse,
)

router = APIRouter(
    prefix="/upi",
    tags=["UPI"],
)


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
)
def get_transactions(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ---------------------------------------------------------
    # 1. Get all active UPI profile IDs belonging to the user
    # ---------------------------------------------------------

    user_profile_ids = [
        profile_id
        for (profile_id,) in (
            db.query(UPIProfile.id)
            .filter(
                UPIProfile.user_id == current_user.id,
                UPIProfile.is_active == True,
            )
            .all()
        )
    ]

    # ---------------------------------------------------------
    # No UPI profiles means no transactions
    # ---------------------------------------------------------

    if not user_profile_ids:
        return TransactionListResponse(
            transactions=[],
            total=0,
            limit=limit,
            offset=offset,
        )

    # ---------------------------------------------------------
    # 2. Create aliases for sender/receiver UPI profiles
    # ---------------------------------------------------------

    sender_profile = aliased(UPIProfile)
    receiver_profile = aliased(UPIProfile)

    # ---------------------------------------------------------
    # 3. Base transaction query
    #
    # Current user must be either:
    #
    # sender OR receiver
    # ---------------------------------------------------------

    base_query = (
        db.query(
            Payment,
            sender_profile.upi_id.label("sender_upi_id"),
            receiver_profile.upi_id.label("receiver_upi_id"),
        )
        .join(
            sender_profile,
            Payment.sender_upi_profile_id == sender_profile.id,
        )
        .join(
            receiver_profile,
            Payment.receiver_upi_profile_id == receiver_profile.id,
        )
        .filter(
            or_(
                Payment.sender_upi_profile_id.in_(user_profile_ids),
                Payment.receiver_upi_profile_id.in_(user_profile_ids),
            )
        )
    )

    # ---------------------------------------------------------
    # 4. Total transaction count
    # ---------------------------------------------------------

    total = base_query.count()

    # ---------------------------------------------------------
    # 5. Fetch transactions
    # ---------------------------------------------------------

    results = (
        base_query.order_by(Payment.created_at.desc()).offset(offset).limit(limit).all()
    )

    transactions = []

    # ---------------------------------------------------------
    # 6. Convert database records to API responses
    # ---------------------------------------------------------

    for payment, sender_upi_id, receiver_upi_id in results:

        sender_is_user = payment.sender_upi_profile_id in user_profile_ids

        receiver_is_user = payment.receiver_upi_profile_id in user_profile_ids

        if sender_is_user and receiver_is_user:
            direction = "SELF"

        elif sender_is_user:
            direction = "DEBIT"

        else:
            direction = "CREDIT"

        transactions.append(
            TransactionResponse(
                transaction_id=payment.transaction_id,
                amount=payment.amount,
                status=payment.status,
                transaction_type=payment.transaction_type,
                sender=sender_upi_id,
                receiver=receiver_upi_id,
                sender_account_id=payment.sender_account_id,
                receiver_account_id=payment.receiver_account_id,
                direction=direction,
                created_at=payment.created_at,
            )
        )

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ---------------------------------------------------------
    # 1. Get user's active UPI profiles
    # ---------------------------------------------------------

    user_profile_ids = [
        profile_id
        for (profile_id,) in (
            db.query(UPIProfile.id)
            .filter(
                UPIProfile.user_id == current_user.id,
                UPIProfile.is_active == True,
            )
            .all()
        )
    ]

    if not user_profile_ids:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    # ---------------------------------------------------------
    # 2. Sender / receiver profile aliases
    # ---------------------------------------------------------

    sender_profile = aliased(UPIProfile)
    receiver_profile = aliased(UPIProfile)

    # ---------------------------------------------------------
    # 3. Find transaction AND verify ownership
    # ---------------------------------------------------------

    result = (
        db.query(
            Payment,
            sender_profile.upi_id.label("sender_upi_id"),
            receiver_profile.upi_id.label("receiver_upi_id"),
        )
        .join(
            sender_profile,
            Payment.sender_upi_profile_id == sender_profile.id,
        )
        .join(
            receiver_profile,
            Payment.receiver_upi_profile_id == receiver_profile.id,
        )
        .filter(
            Payment.transaction_id == transaction_id,
            or_(
                Payment.sender_upi_profile_id.in_(user_profile_ids),
                Payment.receiver_upi_profile_id.in_(user_profile_ids),
            ),
        )
        .first()
    )

    # ---------------------------------------------------------
    # 4. Return 404 for both:
    #
    # transaction doesn't exist
    # OR
    # transaction belongs to another user
    # ---------------------------------------------------------

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    payment, sender_upi_id, receiver_upi_id = result

    # ---------------------------------------------------------
    # 5. Determine transaction direction
    # ---------------------------------------------------------

    sender_is_user = payment.sender_upi_profile_id in user_profile_ids

    receiver_is_user = payment.receiver_upi_profile_id in user_profile_ids

    if sender_is_user and receiver_is_user:
        direction = "SELF"

    elif sender_is_user:
        direction = "DEBIT"

    else:
        direction = "CREDIT"

    # ---------------------------------------------------------
    # 6. Return transaction
    # ---------------------------------------------------------

    return TransactionResponse(
        transaction_id=payment.transaction_id,
        amount=payment.amount,
        status=payment.status,
        transaction_type=payment.transaction_type,
        sender=sender_upi_id,
        receiver=receiver_upi_id,
        sender_account_id=payment.sender_account_id,
        receiver_account_id=payment.receiver_account_id,
        direction=direction,
        created_at=payment.created_at,
    )
