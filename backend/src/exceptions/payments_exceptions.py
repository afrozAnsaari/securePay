class InvalidUPIPinError(Exception):
    """Raised when an incorrect UPI PIN is supplied."""


class TransactionReferenceGenerationError(Exception):
    """Raised when a unique transaction reference cannot be generated."""
