class FraudPaymentDetectedError(Exception):
    """Raise this error when a fraud payment request has been encountered by the API and model."""

    def __init__(self, risk_score: float):
        self.risk_score = risk_score
        super().__init__("Payment rejected by fraud detection.")
