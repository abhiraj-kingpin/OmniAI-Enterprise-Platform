"""Audit logging middleware.

Writes one JSON line per request to data/logs/audit.log: who (best-effort,
decoded from the bearer token if present), what (method + path), the
response status, and latency. Best-effort on purpose — a malformed or
missing token must never block the request, only fall back to "anonymous".
"""

import json
import time
from pathlib import Path

import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings

_LOG_PATH = Path(settings.data_dir) / "logs" / "audit.log"


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

        _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return response
