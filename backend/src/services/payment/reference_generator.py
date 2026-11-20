import secrets

TRANSACTION_REFERENCE_LENGTH = 12
MAX_TRANSACTION_REFERENCE_ATTEMPTS = 3

MIN_TRANSACTION_REFERENCE = 10 ** (TRANSACTION_REFERENCE_LENGTH - 1)

MAX_TRANSACTION_REFERENCE = (10**TRANSACTION_REFERENCE_LENGTH) - 1


def generate_transaction_reference() -> str:
    """
    Random 12-digit reference. Uniqueness is enforced by the database
    (uq_payments_transaction_id); payment_service retries on collision.
    """
    return str(
        secrets.randbelow(MAX_TRANSACTION_REFERENCE - MIN_TRANSACTION_REFERENCE + 1)
        + MIN_TRANSACTION_REFERENCE
    )
