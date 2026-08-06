"""Audit logging middleware.

Writes one JSON line per request to data/logs/audit.log, via a dedicated
rotating-file logger (10MB per file, 5 backups) rather than opening and
writing the file directly on every request: who (best-effort, decoded from
the bearer token if present), what (method + path), the response status,
and latency. Best-effort on purpose — a malformed or missing token must
never block the request, only fall back to "anonymous".
"""

import json
import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings

_LOG_PATH = Path(settings.data_dir) / "logs" / "audit.log"
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

_audit_logger = logging.getLogger("app.audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.propagate = False  # audit entries are structured data, not console noise
if not _audit_logger.handlers:
    _handler = RotatingFileHandler(_LOG_PATH, maxBytes=10_000_000, backupCount=5, encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _audit_logger.addHandler(_handler)


def _best_effort_username(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return "anonymous"
    token = auth[7:]
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub", "anonymous")
    except jwt.InvalidTokenError:
        return "anonymous"


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user": _best_effort_username(request),
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request.client.host if request.client else None,
        }
        _audit_logger.info(json.dumps(entry))

        return response
