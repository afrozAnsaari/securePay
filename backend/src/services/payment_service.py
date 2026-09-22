from fastapi import HTTPException

from src.databases.models import (
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

from src.services.input_validator import resolve_receiver
from src.services.fraud_service import predict_transaction

from src.exceptions.fraud_payment import FraudPaymentDetectedError

from src.utils.enums.FraudDecision import FraudDecision
from src.utils.enums.PaymentStatus import PaymentStatus


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
    # 3. Get + LOCK Sender Account
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
        .with_for_update()
        .first()
    )

    if sender_acc is None:

        raise HTTPException(
            status_code=404,
            detail="Sender account not found.",
        )

    # =========================================================
    # 4. Resolve Receiver
    # =========================================================

    receiver_profile = resolve_receiver(
        db,
        payment_data.receiver,
    )

    # =========================================================
    # 5. Get Receiver Primary Linked Account
    # =========================================================

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

    # =========================================================
    # 6. LOCK Receiver Account
    # =========================================================

    receiver_acc = (
        db.query(Account)
        .filter(
            Account.id == receiver_linked_acc.account_id,
        )
        .with_for_update()
        .first()
    )

    if receiver_acc is None:

        raise HTTPException(
            status_code=404,
            detail="Receiver account not found.",
        )

    # =========================================================
    # 7. Same Account Check
    # =========================================================

    if sender_acc.id == receiver_acc.id:

        raise HTTPException(
            status_code=400,
            detail="Cannot send money to same bank account.",
        )

    # =========================================================
    # 8. Balance Check
    # =========================================================

    if sender_acc.balance < payment_data.amount:

        raise HTTPException(
            status_code=400,
            detail=("Insufficient Balance. " "Transaction Denied"),
        )

    # =========================================================
    # 9. Fraud Detection
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
    # 10. Transfer Funds
    # =========================================================

    sender_acc.balance -= payment_data.amount

    receiver_acc.balance += payment_data.amount

    # =========================================================
    # 11. Create Payment
    # =========================================================

    payment = Payment(
        sender_upi_profile_id=sender_profile.id,
        receiver_upi_profile_id=receiver_profile.id,
        sender_account_id=sender_acc.id,
        receiver_account_id=receiver_acc.id,
        amount=payment_data.amount,
        transaction_type="P2P",
        status=PaymentStatus.SUCCESS.value,
        risk_score=fraud_prediction.risk_score,
        fraud_decision=fraud_decision,
    )

    db.add(payment)

    db.flush()

    # =========================================================
    # 12. Ledger Entries
    # =========================================================

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
