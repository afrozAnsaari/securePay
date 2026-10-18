from datetime import datetime, timezone


def encode_transaction_type(transaction_type: str) -> dict[str, int]:
    """
    Convert business transaction types into the one-hot encoded
    transaction features expected by the fraud model.
    """

    model_transaction_map = {
        "P2P": "TRANSFER",
        "P2M": "PAYMENT",
        "BANK_DEBIT": "DEBIT",
        "ATM_WITHDRAWAL": "CASH_OUT",
    }

    model_type = model_transaction_map.get(transaction_type)

    if model_type is None:
        raise ValueError(f"Unsupported transaction type: {transaction_type}")

    return {
        "type_CASH_OUT": int(model_type == "CASH_OUT"),
        "type_DEBIT": int(model_type == "DEBIT"),
        "type_PAYMENT": int(model_type == "PAYMENT"),
        "type_TRANSFER": int(model_type == "TRANSFER"),
    }


def build_transaction_features(
    sender_account,
    receiver_account,
    amount: float,
    transaction_type: str,
) -> dict:

    features = {
        "step": datetime.now(timezone.utc).hour,
        "amount": amount,
        "oldbalanceOrg": sender_account.balance,
        "newbalanceOrig": sender_account.balance - amount,
        "oldbalanceDest": receiver_account.balance,
        "newbalanceDest": receiver_account.balance + amount,
    }

    features["origBalanceDiff"] = features["oldbalanceOrg"] - features["newbalanceOrig"]

    features.update(encode_transaction_type(transaction_type))

    return features
