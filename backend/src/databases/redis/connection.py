import redis

from src.config import settings

REDIS_URL = settings.REDIS_URL

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    # Fail fast instead of hanging a request (or the readiness check)
    # forever when Redis is unreachable.
    socket_connect_timeout=3,
    socket_timeout=3,
    health_check_interval=30,
)
