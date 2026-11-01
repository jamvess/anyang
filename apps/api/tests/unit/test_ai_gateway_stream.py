"""AI gateway streaming: ai.stream(purpose, input) for tutor_reply (PoC P4-lite).

Behavior from specs/features/tutor/tutor-reply-stream.md §2 "Gateway" and "Provider",
AC-1 to AC-10. Every test uses the fake provider or a stubbed SDK client; none calls a model.
"""

import ast
import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

import app.ai.gateway as gateway_module
from app import stubs
from app.ai.gateway import (
    AIConfigError,
    AIProviderError,
    CallRecord,
    Gateway,
    build_default_gateway,
)
from app.ai.providers.base import ProviderRateLimited
from app.ai.providers.fake import FakeProvider
from app.ai.providers.gemini import GeminiProvider
from app.settings import get_settings

REPO_PROMPTS = get_settings().env.prompts_dir
APP_DIR = Path(__file__).resolve().parents[2] / "app"
MESSAGE = {"message": "สวัสดี"}


def make_gateway(fake: FakeProvider, **config_changes) -> Gateway:
    config = get_settings().ai
    if config_changes:
        config = config.model_copy(update=config_changes)
    return Gateway(config=config, prompts_dir=REPO_PROMPTS, provider=fake)


def tutor_reply_with(**changes) -> dict:
    """``purposes`` with tutor_reply changed, for make_gateway(purposes=...)."""
    purposes = get_settings().ai.purposes
    return purposes | {"tutor_reply": purposes["tutor_reply"].model_copy(update=changes)}


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


# --- AC-1, AC-2 routing and config --------------------------------------------------------


async def test_AI01_stream_sends_purpose_settings_and_rendered_prompt():
    fake = FakeProvider({"tutor_reply": ["ตอบ"]})
    config = get_settings().ai
    purpose = config.purposes["tutor_reply"]

    await collect(make_gateway(fake).stream("tutor_reply", MESSAGE))

    request = fake.requests[0]
    assert request.purpose == "tutor_reply"
    assert request.model == config.tiers[purpose.tier].primary
    assert request.temperature == purpose.temperature
    assert request.max_tokens == purpose.max_tokens
    assert request.thinking == purpose.thinking
    assert "สวัสดี" in request.prompt
    assert "{{" not in request.prompt


@pytest.mark.parametrize("purpose", ["no_such_purpose", "check_answer"])
async def test_AI01_stream_rejects_unknown_or_non_stream_purpose(purpose: str):
    # check_answer exists in config/ai.yaml but has no `stream: true`.
    fake = FakeProvider({purpose: ["x"]})

    with pytest.raises(AIConfigError):
        await collect(make_gateway(fake).stream(purpose, MESSAGE))
    assert fake.requests == []


# --- AC-3 to AC-5 chunks ----------------------------------------------------------------


async def test_AI03_fake_stream_is_deterministic_and_joins_to_script():
    text = "ถูกแล้ว $x^2$ เพราะ $(x-7)(x+7)$"
    fake = FakeProvider({"tutor_reply": [text, text]})
    gateway = make_gateway(fake)

    first = await collect(gateway.stream("tutor_reply", MESSAGE))
    second = await collect(gateway.stream("tutor_reply", MESSAGE))

    assert first == second
    assert "".join(first) == text


async def test_TM08_stream_keeps_latex_chunks_verbatim():
    chunks = ["$\\frac{1}{2}", "\\neq \\theta$"]
    fake = FakeProvider({"tutor_reply": [chunks]})

    assert await collect(make_gateway(fake).stream("tutor_reply", MESSAGE)) == chunks


async def test_AI01_stream_skips_empty_chunks():
    fake = FakeProvider({"tutor_reply": [["ก", "", "ข"]]})

    assert await collect(make_gateway(fake).stream("tutor_reply", MESSAGE)) == ["ก", "ข"]


# --- AC-6 to AC-8 retries and timeout -----------------------------------------------------


async def test_AI01_stream_retries_before_first_chunk():
    config = get_settings().ai
    fake = FakeProvider({"tutor_reply": [RuntimeError("down"), "ตอบได้"]})
    gateway = make_gateway(fake, gateway=config.gateway.model_copy(update={"retries": 1}))

    assert "".join(await collect(gateway.stream("tutor_reply", MESSAGE))) == "ตอบได้"
    assert len(fake.requests) == 2


async def test_AI01_stream_raises_when_every_attempt_fails_before_first_chunk():
    config = get_settings().ai
    fake = FakeProvider({"tutor_reply": [RuntimeError("down"), RuntimeError("still down")]})
    gateway = make_gateway(fake, gateway=config.gateway.model_copy(update={"retries": 1}))

    with pytest.raises(AIProviderError):
        await collect(gateway.stream("tutor_reply", MESSAGE))


@pytest.mark.parametrize(("extra_wait", "retried"), [(0, True), (1, False)])
async def test_AI01_stream_rate_limit_wait_boundary(
    extra_wait: float, retried: bool, sleeps: list[float]
):
    config = get_settings().ai
    gateway_config = config.gateway.model_copy(update={"retries": 1})
    wait = gateway_config.max_retry_wait_seconds + extra_wait
    fake = FakeProvider({"tutor_reply": [ProviderRateLimited("429", retry_after=wait), "ตอบได้"]})
    gateway = make_gateway(fake, gateway=gateway_config)

    if retried:
        assert "".join(await collect(gateway.stream("tutor_reply", MESSAGE))) == "ตอบได้"
        assert sleeps == [wait]
    else:
        with pytest.raises(AIProviderError):
            await collect(gateway.stream("tutor_reply", MESSAGE))
        assert len(fake.requests) == 1


async def test_AI01_stream_no_retry_after_first_chunk():
    config = get_settings().ai
    fake = FakeProvider({"tutor_reply": [["ถูก", RuntimeError("cut")], "ไม่ควรถูกใช้"]})
    gateway = make_gateway(fake, gateway=config.gateway.model_copy(update={"retries": 1}))
    received: list[str] = []

    with pytest.raises(AIProviderError):
        async for chunk in gateway.stream("tutor_reply", MESSAGE):
            received.append(chunk)

    assert received == ["ถูก"]
    assert len(fake.requests) == 1


async def test_AI01_stream_timeout_counts_as_provider_error():
    # A first attempt slower than timeout_s is retried like any provider error (spec §2 step 5).
    config = get_settings().ai

    async def too_slow() -> None:
        await asyncio.sleep(5)

    fake = FakeProvider({"tutor_reply": [[too_slow, "ช้าไป"], "ตอบได้"]})
    gateway = make_gateway(
        fake,
        gateway=config.gateway.model_copy(update={"retries": 1}),
        purposes=tutor_reply_with(timeout_s=0.05),
    )

    assert "".join(await collect(gateway.stream("tutor_reply", MESSAGE))) == "ตอบได้"
    assert len(fake.requests) == 2


# --- AC-9 call record -----------------------------------------------------------------


async def test_AI01_stream_emits_one_call_record_when_complete():
    fake = FakeProvider({"tutor_reply": ["ตอบ"]})
    gateway = make_gateway(fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)

    await collect(gateway.stream("tutor_reply", MESSAGE))

    assert len(records) == 1
    assert records[0].purpose == "tutor_reply"
    assert records[0].prompt_version == "v1"
    assert records[0].status == "ok"


async def test_AI01_stream_emits_one_call_record_when_cut():
    config = get_settings().ai
    fake = FakeProvider({"tutor_reply": [["ถูก", RuntimeError("cut")]]})
    gateway = make_gateway(fake, gateway=config.gateway.model_copy(update={"retries": 0}))
    records: list[CallRecord] = []
    gateway.add_listener(records.append)

    with pytest.raises(AIProviderError):
        await collect(gateway.stream("tutor_reply", MESSAGE))

    assert [r.status for r in records] == ["provider_error"]


async def test_AI01_stream_emits_one_call_record_when_caller_stops():
    fake = FakeProvider({"tutor_reply": [["ถูก", "แล้ว", "ครับ"]]})
    gateway = make_gateway(fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)

    chunks = gateway.stream("tutor_reply", MESSAGE)
    assert await anext(chunks) == "ถูก"
    await chunks.aclose()

    assert [r.status for r in records] == ["provider_error"]


# --- AC-10 config switch -------------------------------------------------------------


async def test_AI02_default_fake_gateway_streams_tutor_reply():
    # AI_PROVIDER=fake (tests/conftest.py). Spec §10 item 4: the stub's tutor tokens, no buddy.
    expected = [
        data["text"]
        for event, data in stubs.events("tutor_reply")
        if event == "token" and data["speaker"] == "tutor"
    ]
    gateway = build_default_gateway()

    first = await collect(gateway.stream("tutor_reply", MESSAGE))
    second = await collect(gateway.stream("tutor_reply", MESSAGE))

    assert first == expected
    assert second == expected  # staging answers every message, not just the first


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


@pytest.mark.parametrize("folder", ["routers", "services"])
def test_AI01_room_code_does_not_import_providers(folder: str):
    for path in (APP_DIR / folder).glob("*.py"):
        for module in _imported_modules(path):
            assert not module.startswith("app.ai.providers"), f"{path.name} imports {module}"
            assert not module.startswith("google"), f"{path.name} imports {module}"


# --- Gemini / Vertex streaming (spec §2 "Provider") -----------------------------------


class StreamingModels:
    def __init__(self, texts: list[str]) -> None:
        self._texts = texts
        self.calls: list[dict] = []

    async def generate_content_stream(self, **kwargs):
        self.calls.append(kwargs)
        texts = self._texts

        async def chunks():
            for text in texts:
                yield type("Chunk", (), {"text": text, "usage_metadata": None})()

        return chunks()


async def test_AI01_gemini_stream_yields_sdk_chunks_without_json_mode():
    provider = GeminiProvider(api_key="test-key")
    models = StreamingModels(["ถูก", "แล้ว $x$"])
    provider._client = type("C", (), {"aio": type("A", (), {"models": models})()})()
    config = get_settings().ai
    gateway = Gateway.live(config, REPO_PROMPTS, {"vertex": provider, "gemini": provider})

    chunks = await collect(gateway.stream("tutor_reply", MESSAGE))

    assert chunks == ["ถูก", "แล้ว $x$"]
    assert models.calls[0]["config"].response_mime_type != "application/json"
