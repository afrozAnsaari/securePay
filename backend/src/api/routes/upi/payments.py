from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.auth.verify_user import get_current_user

from src.databases.database import get_db

from src.databases.models import (
    User,
    Payment,
)

from src.services.rate_limit_service import check_rate_limit

from src.config.rate_limits import RATE_LIMITS

from src.databases.payment_idempotency import PaymentIdempotency

from src.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
)

from src.services.payment_service import (
    process_payment_transaction,
)

from src.services.idempotency_service import (
    generate_request_fingerprint,
    get_idempotency_record,
    store_idempotency_result,
)

router = APIRouter(tags=["Payments"])


@router.post(
    "/upi/pay",
    response_model=PaymentResponse,
    responses={
        400: {
            "description": "Invalid Idempotency-Key",
        },
        409: {
            "description": "Idempotency conflict or payment already processing",
        },
        429: {
            "description": "Too many payment requests",
        },
        500: {
            "description": "Payment associated with the idempotency key was not found.",
        },
        503: {
            "description": "Rate limiting service temporarily unavailable.",
        },
    },
)
def make_payment(
    payment: PaymentCreate,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # =========================================================
    # 1. Validate Idempotency-Key
    # =========================================================

    idempotency_key = idempotency_key.strip()

    if not idempotency_key:

        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key cannot be empty.",
        )

    if len(idempotency_key) > 255:

        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key is too long.",
        )

    # =========================================================
    # 2. RATE LIMIT
    #
    # Redis is used as the rate-limit state store.
    #
    # Each authenticated user gets their own payment bucket.
    #
    # Example:
    #
    # ratelimit:user:1:payment
    # ratelimit:user:2:payment
    #
    # =========================================================

    check_rate_limit(
        key=f"user:{current_user.id}:payment",
        limit=RATE_LIMITS["payment"]["limit"],
        window=RATE_LIMITS["payment"]["window"],
    )

    # =========================================================
    # 3. Generate Request Fingerprint
    # =========================================================

    fingerprint = generate_request_fingerprint(
        receiver=payment.receiver,
        sender_account_id=payment.sender_account_id,
        amount=payment.amount,
    )

    # =========================================================
    # 4. CHECK REDIS IDEMPOTENCY CACHE
    # =========================================================

    cached_record = get_idempotency_record(
        user_id=current_user.id,
        idempotency_key=idempotency_key,
    )

    # =========================================================
    # 5. REDIS CACHE HIT
    # =========================================================

    if cached_record is not None:

        # -----------------------------------------------------
        # Verify that the same idempotency key is being used
        # for the same payment request.
        # -----------------------------------------------------

        if cached_record["request_fingerprint"] != fingerprint:

            raise HTTPException(
                status_code=409,
                detail=("Idempotency-Key was already used  for a different payment."),
            )

        # -----------------------------------------------------
        # Return cached completed result
        # -----------------------------------------------------

        return cached_record["response"]

    # =========================================================
    # 6. REDIS MISS
    #
    # Redis does NOT know whether this is a new payment.
    #
    # PostgreSQL is the durable authority.
    # =========================================================

    existing_record = (
        db.query(PaymentIdempotency)
        .filter(
            PaymentIdempotency.user_id == current_user.id,
            PaymentIdempotency.idempotency_key == idempotency_key,
        )
        .first()
    )

    # =========================================================
    # 7. EXISTING POSTGRESQL IDEMPOTENCY RECORD
    # =========================================================

    if existing_record is not None:

        # -----------------------------------------------------
        # Same key + different payment
        # -----------------------------------------------------

        if existing_record.request_fingerprint != fingerprint:

            raise HTTPException(
                status_code=409,
                detail=("Idempotency-Key was already used for a different payment."),
            )

        # -----------------------------------------------------
        # Payment already completed
        # -----------------------------------------------------

        if existing_record.payment_id is not None:

            saved_payment = (
                db.query(Payment)
                .filter(
                    Payment.id == existing_record.payment_id,
                )
                .first()
            )

            if saved_payment is None:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Payment associated with the idempotency key was not found."
                    ),
                )

            response = {
                "transaction_id": saved_payment.transaction_id,
                "amount": saved_payment.amount,
                "status": saved_payment.status,
                "receiver": payment.receiver,
                "transaction_type": saved_payment.transaction_type,
                "created_at": saved_payment.created_at.isoformat(),
                "message": "Payment already processed.",
            }

            # -------------------------------------------------
            # Re-populate Redis cache.
            #
            # Handles:
            #
            # - Redis expiry
            # - Redis restart
            # - Redis flush
            # -------------------------------------------------

            store_idempotency_result(
                user_id=current_user.id,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                response=response,
            )

            return response

        # -----------------------------------------------------
        # Existing record but no payment_id
        #
        # Another request is currently processing it.
        # -----------------------------------------------------

        raise HTTPException(
            status_code=409,
            detail=(
                "This payment request is already being processed. "
                "Please retry shortly."
            ),
        )

    # =========================================================
    # 8. CREATE NEW POSTGRESQL IDEMPOTENCY RECORD
    # =========================================================

    idempotency_record = PaymentIdempotency(
        user_id=current_user.id,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        payment_id=None,
        status="PROCESSING",
    )

    db.add(idempotency_record)

    # =========================================================
    # 9. TRY TO WIN THE IDEMPOTENCY RACE
    #
    # PostgreSQL UNIQUE constraint:
    #
    #     user_id + idempotency_key
    #
    # determines the winner.
    # =========================================================

    try:

        db.flush()

    except IntegrityError as e:

        # =====================================================
        # WE LOST THE RACE
        #
        # Another request inserted the same key first.
        # =====================================================

        db.rollback()

        constraint_name = getattr(
            getattr(e.orig, "diag", None),
            "constraint_name",
            None,
        )

        if constraint_name != "uq_payment_idempotency_user_key":
            raise

        # print("IDEMPOTENCY FAILURE")
        # print(e)

        # -----------------------------------------------------
        # Fetch the winner's idempotency record
        # -----------------------------------------------------

        existing_record = (
            db.query(PaymentIdempotency)
            .filter(
                PaymentIdempotency.user_id == current_user.id,
                PaymentIdempotency.idempotency_key == idempotency_key,
            )
            .first()
        )

        if existing_record is None:

            raise HTTPException(
                status_code=409,
                detail=("Payment request is currently being processed. Please retry."),
            )

        # -----------------------------------------------------
        # Same key + different payment
        # -----------------------------------------------------

        if existing_record.request_fingerprint != fingerprint:

            raise HTTPException(
                status_code=409,
                detail=("Idempotency-Key was already used for a different payment."),
            )

        # -----------------------------------------------------
        # Winner already completed
        # -----------------------------------------------------

        if existing_record.payment_id is not None:

            saved_payment = (
                db.query(Payment)
                .filter(
                    Payment.id == existing_record.payment_id,
                )
                .first()
            )

            if saved_payment is None:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Payment associated with the idempotency key was not found."
                    ),
                )

            response = {
                "transaction_id": saved_payment.transaction_id,
                "amount": saved_payment.amount,
                "status": saved_payment.status,
                "receiver": payment.receiver,
                "transaction_type": saved_payment.transaction_type,
                "created_at": saved_payment.created_at.isoformat(),
                "message": "Payment already processed.",
            }

            store_idempotency_result(
                user_id=current_user.id,
                idempotency_key=idempotency_key,
                request_fingerprint=fingerprint,
                response=response,
            )

            return response

        # -----------------------------------------------------
        # Winner is still processing
        # -----------------------------------------------------

        raise HTTPException(
            status_code=409,
            detail=(
                "This payment request is already "
                "being processed. Please retry shortly."
            ),
        )

    # =========================================================
    # 10. WE WON THE IDEMPOTENCY RACE
    #
    # This request owns this idempotency key.
    # =========================================================

    try:

        # =====================================================
        # 11. Process Payment
        #
        # No commit happens inside this function.
        # =====================================================

        saved_payment = process_payment_transaction(
            db=db,
            payment_data=payment,
            current_user=current_user,
        )

        # =====================================================
        # 12. Link Idempotency → Payment
        # =====================================================

        idempotency_record.payment_id = saved_payment.id

        idempotency_record.status = "COMPLETED"

        # =====================================================
        # 13. ATOMIC DATABASE COMMIT
        #
        # These all commit together:
        #
        # - idempotency record
        # - sender balance
        # - receiver balance
        # - Payment
        # - debit ledger
        # - credit ledger
        # =====================================================

        db.commit()

        # =====================================================
        # 14. Refresh Payment
        # =====================================================

        db.refresh(saved_payment)

        # =====================================================
        # 15. Build Response
        # =====================================================

        response = {
            "transaction_id": saved_payment.transaction_id,
            "amount": saved_payment.amount,
            "status": saved_payment.status,
            "receiver": payment.receiver,
            "transaction_type": saved_payment.transaction_type,
            "created_at": saved_payment.created_at.isoformat(),
            "message": "Payment successful.",
        }

        # =====================================================
        # 16. CACHE SUCCESSFUL RESULT IN REDIS
        #
        # This happens AFTER DB COMMIT.
        #
        # Therefore Redis can never contain a successful
        # payment that PostgreSQL rolled back.
        # =====================================================

        store_idempotency_result(
            user_id=current_user.id,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            response=response,
        )

        # =====================================================
        # 17. Return Result
        # =====================================================

        return response

    except Exception:

        # =====================================================
        # Payment failed.
        #
        # Roll back:
        #
        # - idempotency record
        # - balance changes
        # - payment
        # - ledger
        #
        # because they are all in the same transaction.
        # =====================================================

        db.rollback()

        raise
