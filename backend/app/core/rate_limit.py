"""Fixed-window rate limiting, per client IP.

Deliberately simple (in-memory counters, one process) rather than a
Redis-backed sliding window — correct for a single-instance deployment, and
the place to swap in `slowapi` + Redis once this runs behind more than one
worker (see the Distributed AI Infrastructure module).
"""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int | None = None) -> None:
        super().__init__(app)
        self.limit = requests_per_minute or settings.rate_limit_per_minute
        self._buckets: dict[str, tuple[int, float]] = defaultdict(lambda: (0, 0.0))

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        count, window_start = self._buckets[client_ip]

        if now - window_start >= _WINDOW_SECONDS:
            count, window_start = 0, now

        count += 1
        self._buckets[client_ip] = (count, window_start)

        if count > self.limit:
            retry_after = max(0, int(_WINDOW_SECONDS - (now - window_start)))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded, slow down."},
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
