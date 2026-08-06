"""Application-wide logging configuration.

Call `configure_logging()` once at process startup. Every module should
then get its own logger via `logging.getLogger(__name__)` rather than
printing directly — this gives consistent timestamps, levels, and a single
place to change formatting or add handlers (e.g. shipping logs to a
collector) without touching call sites.
"""

import logging
import sys

from app.config import settings

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def configure_logging() -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # already configured (e.g. reloader re-entering the module)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    # Noisy third-party loggers that add little at INFO in normal operation.
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
