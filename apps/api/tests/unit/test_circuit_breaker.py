"""Circuit breaker of the AI gateway (specs/features/ai/gateway-guards.md §2.2, AC-12 to AC-25).

Thresholds come from config/ai.yaml → gateway.circuit_breaker, never literals. Time is a fake
clock the test moves. Gateway tests use retries = 0 so one call is one provider request.
"""

import logging
import math
from collections.abc import Iterator
from contextlib import aclosing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.ai.gateway as gateway_module
from app.ai.circuit_breaker import CircuitBreaker
from app.ai.gateway import (
    AIConfigError,
    AIInputError,
    AIProviderError,
    AISchemaError,
    Gateway,
    get_gateway,
)
from app.ai.providers.base import ProviderRequest, ProviderResponse
from app.ai.providers.fake import FakeProvider
from app.main import app
from app.settings import AIConfig, CircuitBreakerConfig, get_settings
from tests.unit.test_ai_gateway import (
    REPO_PROMPTS,
    TOPICS_INPUT,
    VALID_TOPICS,
    TopicsResult,
    write_prompt,
)

CB = get_settings().ai.gateway.circuit_breaker
EPS = 0.001
PURPOSE = "extract_topics_local"
DEGRADE_TEXT = "ระบบช้า ลองส่งอีกทีนะ"  # api.md "ระบบช้า"


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)
    return recorded


def breaker_config(**changes: float) -> CircuitBreakerConfig:
    return CB.model_copy(update=changes)


def ai_config(cb: CircuitBreakerConfig = CB) -> AIConfig:
    config = get_settings().ai
    gateway = config.gateway.model_copy(update={"retries": 0, "circuit_breaker": cb})
    return config.model_copy(update={"gateway": gateway})


def make_gateway(fake: FakeProvider, clock: FakeClock, cb: CircuitBreakerConfig = CB) -> Gateway:
    return Gateway(config=ai_config(cb), prompts_dir=REPO_PROMPTS, provider=fake, clock=clock)


def fill(breaker: CircuitBreaker, ok: int = 0, failed: int = 0) -> None:
    for _ in range(ok):
        assert breaker.acquire()
        breaker.record(ok=True)
    for _ in range(failed):
        assert breaker.acquire()
        breaker.record(ok=False)


def open_breaker(breaker: CircuitBreaker) -> None:
    fill(breaker, failed=CB.minimum_calls)
    assert breaker.state == "open"


# --- the breaker ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("failed", "state"), [(CB.minimum_calls - 1, "closed"), (CB.minimum_calls, "open")]
)
def test_NFRR1_needs_minimum_calls_before_opening(clock, failed: int, state: str) -> None:
    """AC-12"""
    breaker = CircuitBreaker(CB, clock=clock, name="fake")

    fill(breaker, failed=failed)

    assert breaker.state == state


@pytest.mark.parametrize(("below", "state"), [(1, "closed"), (0, "open")])
def test_NFRR1_failure_rate_boundary(clock, below: int, state: str) -> None:
    """AC-13: one failure under the threshold stays closed, at the threshold opens."""
    m = CB.minimum_calls
    failed = math.ceil(CB.failure_rate_threshold * m) - below
    breaker = CircuitBreaker(CB, clock=clock, name="fake")

    fill(breaker, ok=m - failed, failed=failed)

    assert breaker.state == state


def test_NFRR1_rate_counts_only_the_sliding_window(clock) -> None:
    """AC-14: after a full window of successes, failures are a share of the last W calls."""
    w = CB.sliding_window_calls
    needed = math.ceil(CB.failure_rate_threshold * w)
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    fill(breaker, ok=w)

    fill(breaker, failed=needed - 1)
    assert breaker.state == "closed"
    fill(breaker, failed=1)
    assert breaker.state == "open"


@pytest.mark.parametrize(
    ("later", "allowed"), [(CB.open_seconds - EPS, False), (CB.open_seconds + EPS, True)]
)
def test_NFRR1_open_lasts_open_seconds(clock, later: float, allowed: bool) -> None:
    """AC-16"""
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    open_breaker(breaker)

    clock.advance(later)

    assert breaker.acquire() is allowed
    assert breaker.state == ("half_open" if allowed else "open")


def test_NFRR1_half_open_success_closes_and_clears_the_window(clock) -> None:
    """AC-17"""
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    open_breaker(breaker)
    clock.advance(CB.open_seconds + EPS)
    assert breaker.acquire()

    breaker.record(ok=True)

    assert breaker.state == "closed"
    fill(breaker, failed=1)
    assert breaker.state == "closed"


def test_NFRR1_half_open_failure_opens_again(clock) -> None:
    """AC-18"""
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    open_breaker(breaker)
    clock.advance(CB.open_seconds + EPS)
    assert breaker.acquire()

    breaker.record(ok=False)

    assert breaker.state == "open"
    clock.advance(CB.open_seconds - EPS)
    assert not breaker.acquire()
    clock.advance(2 * EPS)
    assert breaker.acquire()


def test_NFRR1_half_open_lets_one_call_through(clock) -> None:
    """AC-19"""
    breaker = CircuitBreaker(CB, clock=clock, name="fake")
    open_breaker(breaker)
    clock.advance(CB.open_seconds + EPS)

    assert breaker.acquire()
    assert not breaker.acquire()


def test_NFRR1_thresholds_come_from_config(clock) -> None:
    """AC-25: minimum_calls 2 and failure_rate_threshold 1.0 open after 2 failures."""
    cb = breaker_config(minimum_calls=2, failure_rate_threshold=1.0)
    breaker = CircuitBreaker(cb, clock=clock, name="fake")

    fill(breaker, failed=1)
    assert breaker.state == "closed"
    fill(breaker, failed=1)
    assert breaker.state == "open"


def test_NFRR1_rate_one_needs_every_call_in_the_window_to_fail(clock) -> None:
    """AC-25: with failure_rate_threshold 1.0 one success in the window keeps it closed."""
    cb = breaker_config(minimum_calls=2, failure_rate_threshold=1.0)
    breaker = CircuitBreaker(cb, clock=clock, name="fake")

    fill(breaker, ok=1, failed=2)

    assert breaker.state == "closed"


def test_NFRR1_state_changes_are_logged_with_the_provider(clock, caplog) -> None:
    """AC-24"""
    breaker = CircuitBreaker(CB, clock=clock, name="vertex")

    with caplog.at_level(logging.WARNING):
        open_breaker(breaker)
        clock.advance(CB.open_seconds + EPS)
        breaker.acquire()
        breaker.record(ok=True)

    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 3  # closed→open, open→half_open, half_open→closed
    assert all("vertex" in m for m in warnings)
    assert ["open" in warnings[0], "half_open" in warnings[1], "closed" in warnings[2]] == [
        True
    ] * 3


# --- the gateway ---------------------------------------------------------------------------------


async def test_NFRR1_open_breaker_fails_call_and_stream_fast(clock, sleeps) -> None:
    """AC-15: no provider request, no backoff wait, no CallRecord."""
    fake = FakeProvider({})
    gateway = make_gateway(fake, clock)
    records = []
    gateway.add_listener(records.append)
    open_breaker(gateway.breaker("fake"))

    with pytest.raises(AIProviderError):
        await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)
    with pytest.raises(AIProviderError):
        async with aclosing(gateway.stream("tutor_reply", {"message": "ข้อ 1"})) as chunks:
            async for _ in chunks:
                pass

    assert fake.requests == []
    assert sleeps == []
    assert records == []


async def test_NFRR1_provider_failures_open_the_breaker(clock) -> None:
    """AC-12 through the gateway: minimum_calls failed calls open it."""
    fake = FakeProvider({PURPOSE: [RuntimeError("down")] * CB.minimum_calls})
    gateway = make_gateway(fake, clock)

    for _ in range(CB.minimum_calls):
        with pytest.raises(AIProviderError):
            await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert gateway.breaker("fake").state == "open"


async def test_NFRR1_schema_errors_do_not_count_as_provider_failures(clock) -> None:
    """AC-20: the model answered, just not in the schema."""
    tries = get_settings().ai.gateway.schema_retries + 1
    fake = FakeProvider({PURPOSE: ["not json"] * tries * CB.minimum_calls})
    gateway = make_gateway(fake, clock)

    for _ in range(CB.minimum_calls):
        with pytest.raises(AISchemaError):
            await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert gateway.breaker("fake").state == "closed"


async def test_NFRR1_config_and_input_errors_are_not_counted(clock) -> None:
    """AC-20: errors raised before a provider is called."""
    cb = breaker_config(minimum_calls=1, failure_rate_threshold=1.0)
    gateway = make_gateway(FakeProvider({}), clock, cb)

    with pytest.raises(AIInputError):
        await gateway.call(PURPOSE, {"file_name": "x"}, TopicsResult)
    with pytest.raises(AIConfigError):
        await gateway.call("no_such_purpose", {}, TopicsResult)

    assert gateway.breaker("fake").state == "closed"


async def test_NFRR1_stream_closed_by_the_caller_counts_as_success(clock) -> None:
    """AC-21"""
    cb = breaker_config(minimum_calls=1, failure_rate_threshold=1.0)
    gateway = make_gateway(FakeProvider({"tutor_reply": ["ก ข ค"]}), clock, cb)

    async with aclosing(gateway.stream("tutor_reply", {"message": "ข้อ 1"})) as chunks:
        async for _ in chunks:
            break

    assert gateway.breaker("fake").state == "closed"


async def test_NFRR1_stream_cut_by_the_provider_counts_as_failure(clock) -> None:
    """AC-21"""
    cb = breaker_config(minimum_calls=1, failure_rate_threshold=1.0)
    gateway = make_gateway(FakeProvider({"tutor_reply": [["ก", RuntimeError("cut")]]}), clock, cb)

    with pytest.raises(AIProviderError):
        async with aclosing(gateway.stream("tutor_reply", {"message": "ข้อ 1"})) as chunks:
            async for _ in chunks:
                pass

    assert gateway.breaker("fake").state == "open"


async def test_NFRR1_breakers_are_per_provider(clock, tmp_path: Path) -> None:
    """AC-22: an open vertex breaker does not stop calls routed to gemini."""
    for purpose in ("p_vertex", "p_gemini"):
        write_prompt(tmp_path, purpose, "ตอบ {{q}}", "q")
    base = ai_config()
    template = base.purposes[PURPOSE]
    tiers = {
        **base.tiers,
        "mid": base.tiers["mid"].model_copy(update={"primary": "vertex:m"}),
        "small": base.tiers["small"].model_copy(update={"primary": "gemini:s"}),
    }
    purposes = {
        **base.purposes,
        "p_vertex": template.model_copy(update={"tier": "mid", "prompt": "v1"}),
        "p_gemini": template.model_copy(update={"tier": "small", "prompt": "v1"}),
    }
    config = base.model_copy(update={"tiers": tiers, "purposes": purposes})

    class Counting:
        def __init__(self) -> None:
            self.calls = 0

        async def generate(self, request: ProviderRequest) -> ProviderResponse:
            self.calls += 1
            return ProviderResponse(text=VALID_TOPICS, tokens_in=1, tokens_out=1)

    vertex, gemini = Counting(), Counting()
    gateway = Gateway.live(
        config=config,
        prompts_dir=tmp_path,
        providers={"vertex": vertex, "gemini": gemini},
        clock=clock,
    )
    open_breaker(gateway.breaker("vertex"))

    with pytest.raises(AIProviderError):
        await gateway.call("p_vertex", {"q": "1"}, TopicsResult)
    await gateway.call("p_gemini", {"q": "1"}, TopicsResult)

    assert (vertex.calls, gemini.calls) == (0, 1)
    assert gateway.breaker("gemini").state == "closed"


# --- what the student sees ---------------------------------------------------------------------


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


def test_NFRR1_open_breaker_degrades_the_tutor_reply(client, clock) -> None:
    """AC-23: the student gets the degrade text and the provider is not called."""
    fake = FakeProvider({})
    gateway = make_gateway(fake, clock)
    open_breaker(gateway.breaker("fake"))
    app.dependency_overrides[get_gateway] = lambda: gateway
    try:
        response = client.post(
            "/sessions/00000000-0000-4000-8000-000000000002/messages", json={"text": "ข้อ 1"}
        )
    finally:
        app.dependency_overrides.pop(get_gateway, None)

    assert response.status_code == 200
    assert DEGRADE_TEXT in response.text
    assert "event: done" in response.text
    assert fake.requests == []
