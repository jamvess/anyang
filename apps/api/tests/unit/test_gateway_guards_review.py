"""Cases found by the self-review of PR #103 (specs/features/ai/gateway-guards.md): stale results,
cancelled calls, a lost half-open trial, the limiter's memory, CORS and the breaker config."""

import asyncio

import pytest
from fastapi.testclient import TestClient

from app.ai.circuit_breaker import CircuitBreaker
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.rate_limit import RateLimiter
from app.settings import CircuitBreakerConfig, get_settings
from tests.unit.test_ai_gateway import TOPICS_INPUT, TopicsResult
from tests.unit.test_circuit_breaker import (
    CB,
    EPS,
    PURPOSE,
    FakeClock,
    breaker_config,
    make_gateway,
    open_breaker,
)

L = get_settings().ai.guards.rate_limit_messages_per_minute


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


def half_open(breaker: CircuitBreaker, clock: FakeClock) -> int:
    """Open the breaker, wait it out and take the trial; returns the trial's generation."""
    open_breaker(breaker)
    clock.advance(CB.open_seconds + EPS)
    assert breaker.acquire()
    return breaker.generation


# --- stale and missing results ------------------------------------------------------------------


def test_NFRR1_result_of_a_call_from_before_the_change_is_dropped(clock) -> None:
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    old = breaker.generation  # a slow call starts while closed
    half_open(breaker, clock)

    breaker.record(ok=True, generation=old)

    assert breaker.state == "half_open"  # the old call did not stand in for the trial
    assert not breaker.acquire()  # and the trial is still the one running


def test_NFRR1_cancelled_trial_frees_the_slot_without_deciding(clock) -> None:
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    trial = half_open(breaker, clock)

    breaker.record(ok=None, generation=trial)

    assert breaker.state == "half_open"
    assert breaker.acquire()  # the next call becomes the trial


def test_NFRR1_no_result_is_not_counted_while_closed(clock) -> None:
    cb = breaker_config(minimum_calls=1, failure_rate_threshold=1.0)
    breaker = CircuitBreaker(cb, clock=clock, name="fake")

    for _ in range(3):
        assert breaker.acquire()
        breaker.record(ok=None)

    assert breaker.state == "closed"


def test_NFRR1_a_lost_trial_expires_and_its_late_result_is_dropped(clock) -> None:
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    lost = half_open(breaker, clock)  # never reports back

    clock.advance(CB.open_seconds - EPS)
    assert not breaker.acquire()
    clock.advance(2 * EPS)
    assert breaker.acquire()  # a new trial
    breaker.record(ok=False, generation=lost)

    assert breaker.state == "half_open"


async def test_NFRR1_cancelled_call_is_not_a_provider_failure(clock) -> None:
    cb = breaker_config(minimum_calls=1, failure_rate_threshold=1.0)
    gateway = make_gateway(FakeProvider({PURPOSE: ["{}"]}, delay_s=30), clock, cb)

    task = asyncio.create_task(gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert gateway.breaker("fake").state == "closed"


async def test_NFRR1_cancelled_trial_stream_does_not_close_the_breaker(clock) -> None:
    gateway = make_gateway(FakeProvider({"tutor_reply": ["ก"]}, delay_s=30), clock)
    breaker = gateway.breaker("fake")
    open_breaker(breaker)
    clock.advance(CB.open_seconds + EPS)

    async def read() -> None:
        async for _ in gateway.stream("tutor_reply", {"message": "ข้อ 1"}):
            pass

    task = asyncio.create_task(read())
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert breaker.state == "half_open"  # not closed: the provider never answered
    assert breaker.acquire()  # and the trial slot is free again


def test_NFRR1_minimum_calls_cannot_exceed_the_window() -> None:
    with pytest.raises(ValueError, match="minimum_calls"):
        CircuitBreakerConfig(
            failure_rate_threshold=CB.failure_rate_threshold,
            minimum_calls=CB.sliding_window_calls + 1,
            sliding_window_calls=CB.sliding_window_calls,
            open_seconds=CB.open_seconds,
        )


# --- rate limiter ------------------------------------------------------------------------------


def test_TM21_keys_seen_once_are_forgotten_after_a_window(clock) -> None:
    limiter = RateLimiter(limit=L, clock=clock)
    for n in range(500):
        limiter.hit(f"ip:203.0.113.{n}")
    assert limiter.keys() == 500

    clock.advance(60 + EPS)
    limiter.hit("ip:198.51.100.1")

    assert limiter.keys() == 1


def test_TM21_browser_can_read_retry_after() -> None:
    origin = get_settings().env.cors_allow_origins[0]
    with TestClient(app) as client:
        response = client.get(
            "/sessions/00000000-0000-4000-8000-000000000002", headers={"Origin": origin}
        )

    exposed = {
        h.strip().lower() for h in response.headers["access-control-expose-headers"].split(",")
    }
    assert "retry-after" in exposed
