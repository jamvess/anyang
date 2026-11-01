"""Circuit breaker of one AI provider (specs/features/ai/gateway-guards.md §2.2,
ai-orchestration.md §2.10). Values from config/ai.yaml → gateway.circuit_breaker.

closed: calls go through; after each result, at least ``minimum_calls`` results in the window of
the last ``sliding_window_calls`` and a failure share ≥ ``failure_rate_threshold`` open it.
open: calls fail fast for ``open_seconds``, then half-open.
half-open: one call goes through; success closes it with an empty window, failure opens it again.
"""

import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Literal

from app.settings import CircuitBreakerConfig

log = logging.getLogger(__name__)

State = Literal["closed", "open", "half_open"]


class CircuitBreaker:
    def __init__(
        self,
        config: CircuitBreakerConfig,
        clock: Callable[[], float] = time.monotonic,
        name: str = "",
    ) -> None:
        self._config = config
        self._clock = clock
        self._name = name
        self._failed: deque[bool] = deque(maxlen=config.sliding_window_calls)
        self._state: State = "closed"
        self._opened_at = 0.0
        self._trial_running = False
        self._lock = threading.Lock()

    @property
    def state(self) -> State:
        return self._state

    def acquire(self) -> bool:
        """Whether a call may go to the provider now. In half-open only the first caller may."""
        with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if self._clock() - self._opened_at < self._config.open_seconds:
                    return False
                self._move("half_open")
            if self._trial_running:
                return False
            self._trial_running = True
            return True

    def record(self, ok: bool) -> None:
        """Result of a call that ``acquire`` let through."""
        with self._lock:
            if self._state == "half_open":
                self._trial_running = False
                if ok:
                    self._failed.clear()
                    self._move("closed")
                else:
                    self._open()
                return
            if self._state == "open":
                return  # a call that started before the breaker opened
            self._failed.append(not ok)
            calls = len(self._failed)
            if (
                calls >= self._config.minimum_calls
                and sum(self._failed) / calls >= self._config.failure_rate_threshold
            ):
                self._open()

    def _open(self) -> None:
        self._opened_at = self._clock()
        self._failed.clear()
        self._move("open")

    def _move(self, state: State) -> None:
        log.warning("circuit breaker %s: %s -> %s", self._name, self._state, state)
        self._state = state
