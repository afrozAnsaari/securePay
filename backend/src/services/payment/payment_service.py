from fastapi import HTTPException

from sqlalchemy.exc import IntegrityError


from src.databases.postgres.models import (
    Account,
    LedgerEntry,
    Payment,
    User,
    UPIProfile,
    LinkedBankAccount,
)

from src.auth.verify_payment_pin import verify_upi_pin

from src.schemas.payment import PaymentCreate
from src.schemas.fraud_prediction import FraudPrediction

from src.services.payment.input_validator import resolve_receiver
from src.services.fraud.fraud_service import predict_transaction

from src.exceptions.fraud_payment import FraudPaymentDetectedError

from src.utils.enums.FraudDecision import FraudDecision
from src.utils.enums.PaymentStatus import PaymentStatus

from src.services.payment.reference_generator import (
    generate_test_transaction_reference,
    generate_transaction_reference,
    MAX_TRANSACTION_REFERENCE_ATTEMPTS,
)

from src.exceptions.payments_exceptions import TransactionReferenceGenerationError


def process_payment_transaction(
    db,
    payment_data: PaymentCreate,
    current_user: User,
) -> Payment:

    if payment_data.amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Please enter a valid amount",
        )

    # =========================================================
    # 1. Get Sender Active UPI Profile
    # =========================================================

    sender_profile = (
        db.query(UPIProfile)
        .filter(
            UPIProfile.id == payment_data.sender_upi_profile_id,
            UPIProfile.user_id == current_user.id,
            UPIProfile.is_active == True,
        )
        .first()
    )

    if sender_profile is None:

        raise HTTPException(
            status_code=404,
            detail="No active UPI Profile found",
        )

    # =========================================================
    # 2. Verify UPI PIN
    # =========================================================

    verify_upi_pin(
        payment_data.upi_pin,
        sender_profile,
    )

    # =========================================================
    # 3. Get Sender Account (Read-only pre-check, no lock)
    # =========================================================

    sender_acc = (
        db.query(Account)
        .join(
            LinkedBankAccount,
            LinkedBankAccount.account_id == Account.id,
        )
        .filter(
            LinkedBankAccount.user_id == current_user.id,
            LinkedBankAccount.account_id == payment_data.sender_account_id,
        )
        .first()
    )

    if sender_acc is None:

        raise HTTPException(
            status_code=404,
            detail="Sender account not found.",
        )

    # =========================================================
    # 4. Resolve Receiver & Primary Account (Read-only, no lock)
    # =========================================================

    receiver_profile = resolve_receiver(
        db,
        payment_data.receiver,
    )

    receiver_linked_acc = (
        db.query(LinkedBankAccount)
        .filter(
            LinkedBankAccount.user_id == receiver_profile.user_id,
            LinkedBankAccount.is_primary == True,
        )
        .first()
    )

    if receiver_linked_acc is None:

        raise HTTPException(
            status_code=404,
            detail=("Receiver cannot accept any payments right now."),
        )

    receiver_acc = (
        db.query(Account)
        .filter(
            Account.id == receiver_linked_acc.account_id,
        )
        .first()
    )

    if receiver_acc is None:

        raise HTTPException(
            status_code=404,
            detail="Receiver account not found.",
        )

    # =========================================================
    # 5. Same Account Check
    # =========================================================

    if sender_acc.id == receiver_acc.id:

        raise HTTPException(
            status_code=400,
            detail="Cannot send money to same bank account.",
        )

    # =========================================================
    # 6. Preliminary Balance Check (Fail-fast before ML inference)
    # =========================================================

    if sender_acc.balance < payment_data.amount:

        raise HTTPException(
            status_code=400,
            detail=("Insufficient Balance. Transaction Denied"),
        )

    # =========================================================
    # 7. Fraud Detection ML Inference
    #
    # Executed BEFORE acquiring database row locks.
    # This prevents DB connection pool exhaustion and avoids
    # holding locks during CPU-bound model computation.
    # =========================================================

    fraud_prediction: FraudPrediction = predict_transaction(
        sender_account=sender_acc,
        receiver_account=receiver_acc,
        amount=payment_data.amount,
        transaction_type="P2P",
    )

    fraud_decision = fraud_prediction.decision

    if fraud_decision == FraudDecision.DECLINED.value:

        raise FraudPaymentDetectedError(risk_score=fraud_prediction.risk_score)

    # =========================================================
    # 8. Acquire Pessimistic Row Locks (with_for_update)
    #
    # Locks are acquired in deterministic order (sorted by account ID)
    # to eliminate deadlocks between concurrent bidirectional transfers.
    # =========================================================

    first_acc_id, second_acc_id = sorted([sender_acc.id, receiver_acc.id])

    db.query(Account).filter(Account.id == first_acc_id).with_for_update().first()
    db.query(Account).filter(Account.id == second_acc_id).with_for_update().first()

    # Re-fetch both accounts now under lock to ensure fresh state
    sender_acc = (
        db.query(Account)
        .filter(Account.id == payment_data.sender_account_id)
        .first()
    )
    receiver_acc = (
        db.query(Account)
        .filter(Account.id == receiver_linked_acc.account_id)
        .first()
    )

    # =========================================================
    # 9. Strict In-Lock Balance Re-Verification
    # =========================================================

    if sender_acc.balance < payment_data.amount:

        raise HTTPException(
            status_code=400,
            detail=("Insufficient Balance. Transaction Denied"),
        )

    # =========================================================
    # 10. Transfer Funds Under Lock
    # =========================================================

    sender_acc.balance -= payment_data.amount

    receiver_acc.balance += payment_data.amount

    # =========================================================
    # 11. Create Payment
    # =========================================================
    # =========================================================
    # 11. Create Payment
    # =========================================================

    # Test implementation

    # =========================================================
    # 11. Create Payment
    # =========================================================

    payment: Payment | None = None

    for attempt in range(MAX_TRANSACTION_REFERENCE_ATTEMPTS):

        transaction_id = generate_transaction_reference()

        # print(f"[TEST] Payment attempt {attempt + 1}: {transaction_id}")

        try:
            with db.begin_nested():

                candidate_payment = Payment(
                    transaction_id=transaction_id,
                    sender_upi_profile_id=sender_profile.id,
                    receiver_upi_profile_id=receiver_profile.id,
                    sender_account_id=sender_acc.id,
                    receiver_account_id=receiver_acc.id,
                    amount=payment_data.amount,
                    transaction_type="P2P",
                    status=PaymentStatus.SUCCESS.value,
                    risk_score=fraud_prediction.risk_score,
                    fraud_decision=fraud_prediction.decision,
                )

                db.add(candidate_payment)

                db.flush()

            payment = candidate_payment
            # print(f"[TEST] Reference accepted: {transaction_id}")

            break

        except IntegrityError as exc:

            constraint_name = getattr(
                getattr(exc.orig, "diag", None),
                "constraint_name",
                None,
            )

            # print(f"[TEST] IntegrityError: {constraint_name}")

            if constraint_name != "uq_payments_transaction_id":
                raise

            # print(f"[TEST] Collision: {transaction_id}")

            if attempt == MAX_TRANSACTION_REFERENCE_ATTEMPTS - 1:
                raise TransactionReferenceGenerationError(
                    f"Unable to generate a unique transaction reference after {MAX_TRANSACTION_REFERENCE_ATTEMPTS} attempts."
                ) from None

    if payment is None:
        raise HTTPException(
            status_code=500,
            detail="Unable to create payment.",
        )

    # =========================================================
    # 12. Ledger Entries
    # =========================================================
    if payment is not None:
        debit = LedgerEntry(
            payment_id=payment.id,
            account_id=sender_acc.id,
            entry_type="DEBIT",
            amount=payment.amount,
        )

        credit = LedgerEntry(
            payment_id=payment.id,
            account_id=receiver_acc.id,
            entry_type="CREDIT",
            amount=payment.amount,
        )

    db.add_all(
        [
            debit,
            credit,
        ]
    )

    # =========================================================
    # IMPORTANT:
    #
    # DO NOT COMMIT HERE.
    #
    # The API will link PaymentIdempotency → Payment and
    # then commit EVERYTHING together.
    # =========================================================

    return payment
