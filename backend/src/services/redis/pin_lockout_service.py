"""
Locks a UPI profile after too many wrong PINs.

A 4-digit PIN has only 10,000 combinations, so without this an attacker
holding a stolen login could simply try them all.

State lives in Redis:
    pin_failures:upi_profile:<id>  -> number of consecutive wrong PINs
The key expires LOCKOUT_SECONDS after the first failure, so the lock
lifts on its own. A correct PIN clears the counter.

Like the rate limiter, this fails closed: if Redis is down we refuse
PIN checks rather than allow unlimited guessing.
"""

import redis
from fastapi import HTTPException

from src.databases.redis import redis_client

MAX_PIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60

# INCR and (on first failure) EXPIRE in one atomic step.
_RECORD_FAILURE_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""


def _key(upi_profile_id: int) -> str:
    return f"pin_failures:upi_profile:{upi_profile_id}"


def _unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="PIN verification is temporarily unavailable. Please try again later.",
    )


def _locked(retry_after: int) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail="Too many incorrect UPI PIN attempts. Your UPI PIN is temporarily locked.",
        headers={"Retry-After": str(max(retry_after, 1))},
    )


def ensure_not_locked(upi_profile_id: int) -> None:
    key = _key(upi_profile_id)

    try:
        failures = redis_client.get(key)
        if failures is not None and int(failures) >= MAX_PIN_ATTEMPTS:
            raise _locked(redis_client.ttl(key))
    except redis.RedisError:
        raise _unavailable()


def record_failure(upi_profile_id: int) -> int:
    try:
        return int(
            redis_client.eval(
                _RECORD_FAILURE_SCRIPT, 1, _key(upi_profile_id), LOCKOUT_SECONDS
            )
        )
    except redis.RedisError:
        raise _unavailable()


def clear_failures(upi_profile_id: int) -> None:
    try:
        redis_client.delete(_key(upi_profile_id))
    except redis.RedisError:
        # The PIN was correct; a stale counter just expires on its own.
        pass
