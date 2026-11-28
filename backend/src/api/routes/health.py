"""
Health checks used by Docker, Render and any load balancer.

/health/live   "Is the process running?"  Never touches a dependency, so a
               slow database can't get a healthy process restarted.
/health/ready  "Can this instance serve requests right now?"  Checks
               Postgres and Redis. Returns 503 when either is down, so the
               platform stops sending traffic here until they are back.
"""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.databases.postgres.database import engine
from src.databases.redis import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
def live():
    return {"status": "ok"}


@router.get("/ready")
def ready():
    checks = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        logger.warning("Readiness: Postgres unavailable: %s", exc.__class__.__name__)
        checks["postgres"] = "unavailable"

    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.warning("Readiness: Redis unavailable: %s", exc.__class__.__name__)
        checks["redis"] = "unavailable"

    healthy = all(value == "ok" for value in checks.values())

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ok" if healthy else "unavailable", "checks": checks},
    )
