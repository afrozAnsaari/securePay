import hashlib
import json

import redis


from src.databases.redis import redis_client

REDIS_URL = "redis://localhost:6379/0"

IDEMPOTENCY_TTL = 60 * 60 * 24


def build_idempotency_key(
    user_id: int,
    idempotency_key: str,
) -> str:

    return f"idempotency:{user_id}:{idempotency_key}"


def generate_request_fingerprint(
    receiver: str,
    sender_account_id: int,
    amount,
) -> str:

    payload = {
        "receiver": receiver.strip().lower(),
        "sender_account_id": sender_account_id,
        "amount": amount,
    }

    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode()).hexdigest()


def get_idempotency_record(
    user_id: int,
    idempotency_key: str,
):

    redis_key = build_idempotency_key(
        user_id,
        idempotency_key,
    )

    try:

        value = redis_client.get(redis_key)

        if value is None:
            return None

        return json.loads(value)

    except (redis.RedisError, json.JSONDecodeError):

        # Redis is only a cache.
        # If Redis fails, PostgreSQL will be used.
        return None


def store_idempotency_result(
    user_id: int,
    idempotency_key: str,
    request_fingerprint: str,
    response: dict,
):

    redis_key = build_idempotency_key(
        user_id,
        idempotency_key,
    )

    record = {
        "request_fingerprint": request_fingerprint,
        "status": "COMPLETED",
        "response": response,
    }

    try:

        redis_client.set(
            redis_key,
            json.dumps(record),
            ex=IDEMPOTENCY_TTL,
        )

    except redis.RedisError:

        # Payment has already been committed to PostgreSQL.
        # Redis failure must NOT make the payment fail.
        pass
