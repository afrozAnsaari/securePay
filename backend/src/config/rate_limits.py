RATE_LIMITS = {
    "login": {
        "limit": 5,
        "window": 60,
    },
    # Per mobile number, independent of IP, so faking X-Forwarded-For
    # or rotating IPs can't be used to guess one account's password.
    "login_account": {
        "limit": 10,
        "window": 900,
    },
    "register": {
        "limit": 5,
        "window": 3600,
    },
    "refresh": {
        "limit": 10,
        "window": 60,
    },
    "payment": {
        "limit": 10,
        "window": 60,
    },
    "balance": {
        "limit": 10,
        "window": 60,
    },
    "accounts": {
        "limit": 30,
        "window": 60,
    },
    "transactions": {
        "limit": 60,
        "window": 60,
    },
    "lba": {
        "limit": 30,
        "window": 60,
    },
}
