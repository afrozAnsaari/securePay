import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"


LOG_FORMAT = "%(asctime)s | %(levelname)s |%(name)s | %(message)s"


def setup_logging():
    formatter = logging.Formatter(LOG_FORMAT)

    root_logger = logging.getLogger()

    # Prevent duplicate handlers if setup_logging()
    # is called more than once.
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)

    # -------------------------
    # stdout handler
    # -------------------------

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # -------------------------
    # File handler
    # -------------------------

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # -------------------------
    # Register handlers
    # -------------------------

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
