"""Rate limit of the messages a user sends in the tutor room (specs/features/ai/gateway-guards.md
§2.1 · ai-orchestration.md §2.9 Limits).

``guards.rate_limit_messages_per_minute`` messages per sliding 60-second window, counted per
``user_id`` (per client IP without a token). The counts live in memory, so each Cloud Run
instance counts on its own and a restart starts again (spec §10 item 4).
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from functools import cache
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Request

from app.auth import AuthContext, get_auth
from app.models.error import ErrorResponse
from app.settings import get_settings

WINDOW_SECONDS = 60.0  # the "per minute" of the config key's name


class RateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self._window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._last_sweep = clock()
        self._lock = threading.Lock()

    def hit(self, key: str) -> int | None:
        """Count one message of ``key``. ``None`` when it may go through, else the whole
        seconds until the oldest counted message leaves the window (at least 1). A refused
        message is not counted (spec AC-4)."""
        now = self._clock()
        with self._lock:
            self._sweep(now)
            hits = self._hits.setdefault(key, deque())
            while hits and hits[0] <= now - self._window:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(1, math.ceil(hits[0] + self._window - now))
            hits.append(now)
            return None

    def _sweep(self, now: float) -> None:
        """Once a window, forget keys with no message in the window, so keys that are
        seen once (an anonymous client with a new IP each time) do not pile up."""
        if now - self._last_sweep < self._window:
            return
        self._last_sweep = now
        cutoff = now - self._window
        for key in [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]:
            del self._hits[key]

    def keys(self) -> int:
        """How many keys are held (for tests and logs)."""
        return len(self._hits)


@cache
def get_rate_limiter() -> RateLimiter:
    """The process's limiter. Routers take it as a dependency, so tests can swap the clock."""
    return RateLimiter(limit=get_settings().ai.guards.rate_limit_messages_per_minute)


def _client_ip(request: Request) -> str:
    # A client can send its own X-Forwarded-For and Google keeps it in front of the address it
    # adds, so the first value is the client's word. Good enough as a stop-gap: live AI stays off
    # while AUTH_REQUIRED=false (spec §10 item 1).
    forwarded = request.headers.get("x-forwarded-for", "")
    first = forwarded.split(",", 1)[0].strip()
    if first:
        return first
    return request.client.host if request.client else "unknown"


# OpenAPI of the endpoints that use chat_rate_limit.
RATE_LIMITED_DOCS: dict[int | str, dict[str, Any]] = {
    429: {"model": ErrorResponse, "description": "rate_limited; Retry-After gives the seconds"},
}


async def chat_rate_limit(
    request: Request,
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    limiter: Annotated[RateLimiter, Depends(get_rate_limiter)],
) -> None:
    """Dependency of the endpoints that send a user message: 429 ``rate_limited`` with
    ``Retry-After`` over the limit. It runs before the body's fields are checked, so a body
    that fails validation counts too (spec §10 item 3). A body that is not JSON at all is
    refused by FastAPI before dependencies run, so it is not counted; it never reaches the AI."""
    key = f"user:{auth.user_id}" if auth else f"ip:{_client_ip(request)}"
    retry_after = limiter.hit(key)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail=f"Too many messages; try again in {retry_after} s",
            headers={"Retry-After": str(retry_after)},
        )
