"""Circuit breaker of one AI provider (specs/features/ai/gateway-guards.md §2.2,
ai-orchestration.md §2.10). Values from config/ai.yaml → gateway.circuit_breaker.

closed: calls go through; after each result, at least ``minimum_calls`` results in the window of
the last ``sliding_window_calls`` and a failure share ≥ ``failure_rate_threshold`` open it.
open: calls fail fast for ``open_seconds``, then half-open.
half-open: one call goes through; success closes it with an empty window, failure opens it again.

Every state change starts a new ``generation``. A result recorded with an older generation (a
slow call that began before the change) is dropped, so it cannot stand in for the half-open
trial. A trial that never reports back (a stream dropped without closing) expires after
``open_seconds`` and the next call becomes the trial.
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
        self._generation = 0
        self._opened_at = 0.0
        self._trial_started: float | None = None
        self._lock = threading.Lock()

    @property
    def state(self) -> State:
        return self._state

    @property
    def generation(self) -> int:
        """Pass it back to ``record`` so a result lands in the state its call started in."""
        return self._generation

    def acquire(self) -> bool:
        """Whether a call may go to the provider now. In half-open only the trial may."""
        with self._lock:
            now = self._clock()
            if self._state == "closed":
                return True
            if self._state == "open":
                if now - self._opened_at < self._config.open_seconds:
                    return False
                self._move("half_open")
            elif self._trial_started is not None:
                if now - self._trial_started < self._config.open_seconds:
                    return False
                self._generation += 1  # the lost trial's late result no longer counts
            self._trial_started = now
            return True

    def record(self, ok: bool | None, generation: int | None = None) -> None:
        """Result of a call that ``acquire`` let through: ``True`` the provider answered,
        ``False`` it failed, ``None`` no result (the caller cancelled it). ``generation`` is
        the value read right after ``acquire``; without it the result is taken as current."""
        with self._lock:
            if generation is not None and generation != self._generation:
                return  # the call began before the last state change
            if self._state == "half_open":
                self._trial_started = None
                if ok is True:
                    self._failed.clear()
                    self._move("closed")
                elif ok is False:
                    self._open()
                return
            if self._state == "open" or ok is None:
                return
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
        self._generation += 1
