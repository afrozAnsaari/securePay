"""
Logging setup for SecurePay.

Environment variables:
    LOG_FORMAT   "text" (default, easy to read locally) or "json"
                 (one JSON object per line, for log collectors in production).
    LOG_TO_FILE  "true" also writes to backend/logs/app.log (default false).
                 In a container leave it off: logs go to stdout and the
                 platform (Docker, Render) collects them.
    LOG_LEVEL    default INFO.

Every log line carries the current request's ID (see request_id_ctx), so
all lines from one HTTP request can be found together.
"""

import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

TEXT_FORMAT = "%(asctime)s | %(levelname)s | %(request_id)s | %(name)s | %(message)s"

# Set by the request-ID middleware in app.py for the duration of a request.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """Adds `record.request_id` so formatters can print it."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def setup_logging():
    root_logger = logging.getLogger()

    # Prevent duplicate handlers if setup_logging() is called more than once.
    if any(isinstance(f, RequestIdFilter) for h in root_logger.handlers for f in h.filters):
        return

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root_logger.setLevel(level)

    if os.getenv("LOG_FORMAT", "text").strip().lower() == "json":
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(TEXT_FORMAT)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if _env_bool("LOG_TO_FILE"):
        LOG_DIR.mkdir(exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                LOG_FILE,
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
        )

    for handler in handlers:
        handler.setLevel(level)
        handler.setFormatter(formatter)
        handler.addFilter(RequestIdFilter())
        root_logger.addHandler(handler)
