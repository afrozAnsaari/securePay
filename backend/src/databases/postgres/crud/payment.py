from sqlalchemy.orm import Session

from src.databases.postgres.models.payment import Payment


def create_payment(db: Session, payment_data: dict, fraud_result: dict):
    payment = Payment(
        merchant_id=payment_data["merchant_id"],
        transaction_type=payment_data["type"],
        amount=payment_data["amount"],
        status=fraud_result["decision"],
        risk_score=fraud_result["risk_score"],
        fraud_decision=fraud_result["decision"],
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment
