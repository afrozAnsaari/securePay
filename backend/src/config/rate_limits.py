RATE_LIMITS = {
    "login": {
        "limit": 5,
        "window": 60,
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
        # This is temporary change: limit 10->3
        "limit": 3,
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
        # Changed temporarily for testing 30->5
        "limit": 5,
        "window": 60,
    },
}
