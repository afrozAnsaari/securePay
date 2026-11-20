class InvalidUPIPinError(Exception):
    """Raised when an incorrect UPI PIN is supplied."""

    def __init__(self, attempts_left: int | None = None):
        self.attempts_left = attempts_left
        super().__init__("Invalid UPI PIN")


class TransactionReferenceGenerationError(Exception):
    """Raised when a unique transaction reference cannot be generated."""


def invalid_pin_message(attempts_left: int | None) -> str:
    if attempts_left is None:
        return "Invalid UPI PIN"
    if attempts_left == 0:
        return "Invalid UPI PIN. Your UPI PIN is now temporarily locked."
    return f"Invalid UPI PIN. {attempts_left} attempt(s) left."
