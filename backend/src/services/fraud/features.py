from datetime import datetime, timezone

# PaySim's transaction types, used directly by the model.
PAYSIM_TYPES = ("CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER")

# How this app's transaction types map onto PaySim's.
APP_TO_PAYSIM_TYPE = {
    "P2P": "TRANSFER",
    "P2M": "PAYMENT",
    "BANK_DEBIT": "DEBIT",
    "ATM_WITHDRAWAL": "CASH_OUT",
}


def current_paysim_step(now: datetime | None = None) -> int:
    """
    PaySim's `step` is "hours since the start of a 30-day simulation" (1-743).
    The model was trained on that, so we use hours since the start of the
    current month instead of the hour of the day (0-23).
    """

    now = now or datetime.now(timezone.utc)
    return min((now.day - 1) * 24 + now.hour + 1, 743)


def encode_paysim_type(paysim_type: str) -> dict[str, int]:
    paysim_type = paysim_type.upper()

    if paysim_type not in PAYSIM_TYPES:
        raise ValueError(f"Unsupported PaySim transaction type: {paysim_type}")

    return {f"type_{t}": int(paysim_type == t) for t in PAYSIM_TYPES}


def encode_transaction_type(transaction_type: str) -> dict[str, int]:
    """
    Convert business transaction types into the one-hot encoded
    transaction features expected by the fraud model.
    """

    model_type = APP_TO_PAYSIM_TYPE.get(transaction_type)

    if model_type is None:
        raise ValueError(f"Unsupported transaction type: {transaction_type}")

    return encode_paysim_type(model_type)


def build_raw_features(
    *,
    step: int,
    amount: float,
    old_balance_org: float,
    new_balance_orig: float,
    old_balance_dest: float,
    new_balance_dest: float,
    type_encoding: dict[str, int],
) -> dict:
    return {
        "step": step,
        "amount": amount,
        "oldbalanceOrg": old_balance_org,
        "newbalanceOrig": new_balance_orig,
        "oldbalanceDest": old_balance_dest,
        "newbalanceDest": new_balance_dest,
        "origBalanceDiff": old_balance_org - new_balance_orig,
        **type_encoding,
    }


def build_transaction_features(
    sender_account,
    receiver_account,
    amount,
    transaction_type: str,
) -> dict:

    sender_balance = float(sender_account.balance)
    receiver_balance = float(receiver_account.balance)
    float_amount = float(amount)

    return build_raw_features(
        step=current_paysim_step(),
        amount=float_amount,
        old_balance_org=sender_balance,
        new_balance_orig=sender_balance - float_amount,
        old_balance_dest=receiver_balance,
        new_balance_dest=receiver_balance + float_amount,
        type_encoding=encode_transaction_type(transaction_type),
    )
