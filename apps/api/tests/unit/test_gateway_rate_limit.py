"""The gateway waits longer on a provider 429 (specs/features/ai/gateway-rate-limit-backoff.md
§2.1-2.2 · AC-1 to AC-8).

No network: the fake provider raises ``ProviderRateLimited`` from its script and ``_sleep`` is
recorded instead of slept. The waits come from config/ai.yaml unless a test sets its own.

Interfaces these tests expect (to be built by /implement-feature):
- ``GatewayConfig.rate_limit_waits_seconds`` and ``rate_limit_waits_stream_seconds``
  (``list[float]``, every value >= 0, both required)
- ``app.ai.gateway.AIRateLimitedError``, a subclass of ``AIProviderError``
"""

from collections.abc import AsyncIterator

import pytest
from pydantic import ValidationError

import app.ai.gateway as gateway_module
from app.ai.gateway import AIProviderError, AIRateLimitedError, CallRecord, Gateway
from app.ai.providers.base import ProviderRateLimited
from app.ai.providers.fake import FakeProvider
from app.settings import GatewayConfig, get_settings
from tests.unit.test_ai_gateway import (
    TOPICS_INPUT,
    VALID_TOPICS,
    FakeEmbedder,
    TopicsResult,
)

CONFIG = get_settings().ai
PURPOSE = "extract_topics_local"  # any purpose without `stream: true`
MESSAGE = {"message": "สวัสดี"}


def rate_limited(retry_after: float | None = None) -> ProviderRateLimited:
    return ProviderRateLimited("429 RESOURCE_EXHAUSTED", retry_after=retry_after)


def make_gateway(provider, **gateway_changes) -> Gateway:
    config = CONFIG.model_copy(
        update={
            "gateway": CONFIG.gateway.model_copy(update=gateway_changes),
            # Fakes return short vectors (see test_ai_gateway.make_gateway).
            "embedding": CONFIG.embedding.model_copy(update={"dimensions": None}),
        }
    )
    return Gateway(config=config, prompts_dir=get_settings().env.prompts_dir, provider=provider)


async def collect(chunks: AsyncIterator[str]) -> list[str]:
    return [chunk async for chunk in chunks]


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retry waits are recorded instead of slept, so no test waits for real."""
    recorded: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)
    return recorded


# --- AC-1, AC-2 call ------------------------------------------------------------------------


async def test_NFRR1_call_waits_the_table_after_each_429_then_answers(sleeps: list[float]):
    # AC-1
    waits = CONFIG.gateway.rate_limit_waits_seconds
    fake = FakeProvider({PURPOSE: [rate_limited()] * len(waits) + [VALID_TOPICS]})

    result = await make_gateway(fake).call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert result.topics[0].name == "ลิมิต (Limit)"
    assert sleeps == list(waits)
    assert len(fake.requests) == len(waits) + 1


async def test_NFRR1_call_gives_up_after_the_last_429_without_waiting(sleeps: list[float]):
    # AC-2 (boundary: one 429 more than the table)
    waits = CONFIG.gateway.rate_limit_waits_seconds
    fake = FakeProvider({PURPOSE: [rate_limited()] * (len(waits) + 1) + [VALID_TOPICS]})

    with pytest.raises(AIRateLimitedError) as raised:
        await make_gateway(fake).call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert isinstance(raised.value, AIProviderError)
    assert PURPOSE in str(raised.value)
    assert sleeps == list(waits)
    assert len(fake.requests) == len(waits) + 1


def test_NFRR1_the_tables_in_config_are_the_agreed_ones():
    # §2.1 · the values Junior and Jam agreed for the video (17-19 Nov)
    assert CONFIG.gateway.rate_limit_waits_seconds == [5, 15, 30]
    assert CONFIG.gateway.rate_limit_waits_stream_seconds == [5]


# --- AC-3 stream ----------------------------------------------------------------------------


async def test_NFRR1_stream_waits_the_stream_table_before_the_first_chunk(sleeps: list[float]):
    # AC-3
    waits = CONFIG.gateway.rate_limit_waits_stream_seconds
    fake = FakeProvider({"tutor_reply": [rate_limited()] * len(waits) + ["ตอบได้"]})

    text = "".join(await collect(make_gateway(fake).stream("tutor_reply", MESSAGE)))

    assert text == "ตอบได้"
    assert sleeps == list(waits)
    assert len(fake.requests) == len(waits) + 1


async def test_NFRR1_stream_gives_up_after_the_stream_table(sleeps: list[float]):
    # AC-3 (boundary)
    waits = CONFIG.gateway.rate_limit_waits_stream_seconds
    fake = FakeProvider({"tutor_reply": [rate_limited()] * (len(waits) + 1) + ["ไม่ควรถูกใช้"]})
    received: list[str] = []

    with pytest.raises(AIRateLimitedError):
        async for chunk in make_gateway(fake).stream("tutor_reply", MESSAGE):
            received.append(chunk)

    assert received == []
    assert sleeps == list(waits)
    assert len(fake.requests) == len(waits) + 1


# --- AC-4 embed -----------------------------------------------------------------------------


class RateLimitedEmbedder(FakeEmbedder):
    """429 on the first ``failures`` requests, then vectors as FakeEmbedder."""

    def __init__(self, failures: int) -> None:
        super().__init__()
        self._429s = failures

    async def embed(self, request):
        if self._429s:
            self._429s -= 1
            self.requests.append(request)
            raise rate_limited()
        return await super().embed(request)


async def test_NFRR1_embed_uses_the_non_stream_table(sleeps: list[float]):
    # AC-4
    embedder = RateLimitedEmbedder(failures=1)

    vectors = await make_gateway(embedder).embed(["a"], role="query")

    assert len(vectors) == 1
    assert sleeps == CONFIG.gateway.rate_limit_waits_seconds[:1]


# --- AC-5 the table comes from config ---------------------------------------------------------


async def test_NFRR1_call_follows_a_table_set_in_config(sleeps: list[float]):
    # AC-5
    fake = FakeProvider({PURPOSE: [rate_limited()] * 3 + [VALID_TOPICS]})

    with pytest.raises(AIRateLimitedError):
        await make_gateway(fake, rate_limit_waits_seconds=[1, 2]).call(
            PURPOSE, TOPICS_INPUT, TopicsResult
        )

    assert sleeps == [1, 2]
    assert len(fake.requests) == 3


async def test_NFRR1_an_empty_table_means_no_retry_on_429(sleeps: list[float]):
    # AC-5
    fake = FakeProvider({PURPOSE: [rate_limited(), VALID_TOPICS]})

    with pytest.raises(AIRateLimitedError):
        await make_gateway(fake, rate_limit_waits_seconds=[]).call(
            PURPOSE, TOPICS_INPUT, TopicsResult
        )

    assert sleeps == []
    assert len(fake.requests) == 1


@pytest.mark.parametrize("key", ["rate_limit_waits_seconds", "rate_limit_waits_stream_seconds"])
def test_NFRR1_a_negative_wait_does_not_load(key: str):
    # AC-5
    values = CONFIG.gateway.model_dump() | {key: [5, -1]}

    with pytest.raises(ValidationError):
        GatewayConfig.model_validate(values)


@pytest.mark.parametrize("key", ["rate_limit_waits_seconds", "rate_limit_waits_stream_seconds"])
def test_NFRR1_a_missing_table_does_not_load(key: str):
    # §2.1 (strict like every other key)
    values = CONFIG.gateway.model_dump()
    del values[key]

    with pytest.raises(ValidationError):
        GatewayConfig.model_validate(values)


# --- AC-6 the wait the provider asks for ----------------------------------------------------------

TABLE = [5, 15, 30]


@pytest.mark.parametrize(
    ("retry_after", "waited"),
    [
        pytest.param(None, 5, id="no retry_after: the slot"),
        pytest.param(3, 5, id="shorter than the slot: the slot"),
        pytest.param(8, 8, id="longer than the slot: the provider"),
        pytest.param(20, 20, id="above max_retry_wait_seconds: still waits"),
        pytest.param(30, 30, id="= the largest slot: waits"),
    ],
)
async def test_NFRR1_call_waits_the_longer_of_the_slot_and_retry_after(
    retry_after: float | None, waited: float, sleeps: list[float]
):
    # AC-6
    fake = FakeProvider({PURPOSE: [rate_limited(retry_after), VALID_TOPICS]})
    gateway = make_gateway(fake, rate_limit_waits_seconds=TABLE, max_retry_wait_seconds=10)

    await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert sleeps == [waited]
    assert len(fake.requests) == 2


async def test_NFRR1_call_gives_up_when_retry_after_is_above_the_largest_slot(
    sleeps: list[float],
):
    # AC-6 (boundary: largest slot + 1)
    fake = FakeProvider({PURPOSE: [rate_limited(max(TABLE) + 1), VALID_TOPICS]})
    gateway = make_gateway(fake, rate_limit_waits_seconds=TABLE, max_retry_wait_seconds=10)

    with pytest.raises(AIRateLimitedError):
        await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert sleeps == []
    assert len(fake.requests) == 1


async def test_NFRR1_a_later_slot_longer_than_retry_after_is_kept(sleeps: list[float]):
    # AC-6: the third 429 asks for 20 s, its slot is 30 s
    script = [rate_limited(), rate_limited(), rate_limited(20), VALID_TOPICS]
    fake = FakeProvider({PURPOSE: script})
    gateway = make_gateway(fake, rate_limit_waits_seconds=TABLE, max_retry_wait_seconds=10)

    await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert sleeps == [5, 15, 30]


@pytest.mark.parametrize(("extra", "retried"), [(0, True), (1, False)])
async def test_NFRR1_stream_retry_after_boundary_is_the_largest_stream_slot(
    extra: float, retried: bool, sleeps: list[float]
):
    # AC-6 (stream table [5]: 5 waits, 6 gives up)
    stream_table = [5]
    retry_after = max(stream_table) + extra
    fake = FakeProvider({"tutor_reply": [rate_limited(retry_after), "ตอบได้"]})
    gateway = make_gateway(fake, rate_limit_waits_stream_seconds=stream_table)

    if retried:
        assert "".join(await collect(gateway.stream("tutor_reply", MESSAGE))) == "ตอบได้"
        assert sleeps == [retry_after]
    else:
        with pytest.raises(AIRateLimitedError):
            await collect(gateway.stream("tutor_reply", MESSAGE))
        assert sleeps == []
        assert len(fake.requests) == 1


async def test_NFRR1_other_errors_still_use_max_retry_wait_seconds(sleeps: list[float]):
    # AC-6b: unchanged behavior for errors that are not 429
    fake = FakeProvider({PURPOSE: [RuntimeError("503"), VALID_TOPICS]})
    gateway = make_gateway(fake, retries=1, retry_backoff_seconds=12, max_retry_wait_seconds=10)

    with pytest.raises(AIProviderError) as raised:
        await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert not isinstance(raised.value, AIRateLimitedError)
    assert sleeps == []
    assert len(fake.requests) == 1


# --- AC-7 other errors keep their own budget ---------------------------------------


async def test_NFRR1_timeouts_still_use_retries_and_retry_backoff(sleeps: list[float]):
    # AC-7
    retries = CONFIG.gateway.retries
    backoff = CONFIG.gateway.retry_backoff_seconds
    fake = FakeProvider({PURPOSE: [TimeoutError()] * (retries + 1) + [VALID_TOPICS]})

    with pytest.raises(AIProviderError) as raised:
        await make_gateway(fake).call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert not isinstance(raised.value, AIRateLimitedError)
    assert sleeps == [backoff] * retries
    assert len(fake.requests) == retries + 1


async def test_NFRR1_a_429_and_a_timeout_spend_separate_budgets(sleeps: list[float]):
    # AC-7
    backoff = CONFIG.gateway.retry_backoff_seconds
    waits = CONFIG.gateway.rate_limit_waits_seconds
    fake = FakeProvider({PURPOSE: [rate_limited(), TimeoutError(), VALID_TOPICS]})

    await make_gateway(fake, retries=1).call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert sleeps == [waits[0], backoff]
    assert len(fake.requests) == 3


async def test_NFRR1_the_error_after_giving_up_follows_the_last_error(sleeps: list[float]):
    # AC-7 (§2.2 item 4): the 429 budget is not spent, the timeout budget is
    fake = FakeProvider({PURPOSE: [rate_limited(), TimeoutError(), TimeoutError()]})

    with pytest.raises(AIProviderError) as raised:
        await make_gateway(fake, retries=1).call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert not isinstance(raised.value, AIRateLimitedError)
    assert len(fake.requests) == 3


# --- AC-8 one record, one breaker outcome ---------------------------------------


async def test_NFRR1_giving_up_on_429_writes_one_record_and_one_breaker_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    # AC-8
    waits = CONFIG.gateway.rate_limit_waits_seconds
    fake = FakeProvider({PURPOSE: [rate_limited()] * (len(waits) + 1)})
    gateway = make_gateway(fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)
    outcomes: list[bool | None] = []
    breaker = gateway.breaker("fake")
    record = breaker.record
    monkeypatch.setattr(
        breaker, "record", lambda ok, generation=None: (outcomes.append(ok), record(ok, generation))
    )

    with pytest.raises(AIRateLimitedError):
        await gateway.call(PURPOSE, TOPICS_INPUT, TopicsResult)

    assert [r.status for r in records] == ["provider_error"]
    assert outcomes == [False]
