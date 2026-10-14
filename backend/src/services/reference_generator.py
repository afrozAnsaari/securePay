import secrets


from fastapi import HTTPException


from sqlalchemy.orm import Session

from src.databases.models import Payment

TRANSACTION_REFERENCE_LENGTH = 10
MAX_TRANSACTION_REFERENCE_ATTEMPTS = 3

MIN_TRANSACTION_REFERENCE = 10 ** (TRANSACTION_REFERENCE_LENGTH - 1)

MAX_TRANSACTION_REFERENCE = (10**TRANSACTION_REFERENCE_LENGTH) - 1


def generate_transaction_reference() -> str:
    return str(
        secrets.randbelow(MAX_TRANSACTION_REFERENCE - MIN_TRANSACTION_REFERENCE + 1)
        + MIN_TRANSACTION_REFERENCE
    )


# =========================================================
# TEMPORARY COLLISION TEST
# REMOVE/COMMENT AFTER TESTING
# =========================================================
_test_references = [
    "5831047291",
    "5831047291",
    "8174026395",
]


_test_reference_index = 0


def generate_test_transaction_reference() -> str:
    global _test_reference_index

    if _test_reference_index >= len(_test_references):
        raise RuntimeError("Test transaction reference sequence exhausted")

    reference = _test_references[_test_reference_index]

    print(f"[TEST] Generated reference {_test_reference_index + 1}: {reference}")

    _test_reference_index += 1

    return reference


def generate_unique_transaction_reference(db: Session) -> str:
    for _ in range(3):
        transaction_id = generate_transaction_reference()

        existing = (
            db.query(Payment.id)
            .filter(Payment.transaction_id == transaction_id)
            .first()
        )

        if existing is None:
            return transaction_id

    raise HTTPException(
        status_code=500,
        detail=(
            "Unable to generate a unique transaction reference. "
            "Please try again later."
        ),
    )
