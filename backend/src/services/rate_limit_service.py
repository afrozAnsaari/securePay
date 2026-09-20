import time
import uuid

import redis
from fastapi import HTTPException

from src.databases.redis import redis_client

RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_start = tonumber(ARGV[2])
local request_id = ARGV[3]
local limit = tonumber(ARGV[4])
local window = tonumber(ARGV[5])

redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

local count = redis.call('ZCARD', key)

if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')

    if #oldest >= 2 then
        local oldest_timestamp = tonumber(oldest[2])
        local retry_after = window - (now - oldest_timestamp)

        if retry_after < 1 then
            retry_after = 1
        end

        return {0, retry_after}
    end

    return {0, window}
end

redis.call('ZADD', key, now, request_id)
redis.call('EXPIRE', key, window)

return {1, 0}
"""


def check_rate_limit(key: str, limit: int, window: int) -> None:

    if limit <= 0:
        raise ValueError("Rate limit must be greater than zero.")

    if window <= 0:
        raise ValueError("Rate-limit window must be greater than zero.")

    current_time = int(time.time())
    window_start = current_time - window

    redis_key = f"ratelimit:{key}"
    request_id = str(uuid.uuid4())

    try:
        result = redis_client.eval(
            RATE_LIMIT_SCRIPT,
            1,
            redis_key,
            current_time,
            window_start,
            request_id,
            limit,
            window,
        )

    except redis.RedisError:
        raise HTTPException(
            status_code=503,
            detail="Rate limiting service temporarily unavailable.",
        )

    allowed = int(result[0])
    retry_after = int(result[1])

    if allowed == 0:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later.",
            headers={
                "Retry-After": str(retry_after),
            },
        )
