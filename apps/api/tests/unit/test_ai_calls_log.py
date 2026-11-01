"""AI-04: the gateway's call records go to a JSON log line and, with a tenant, to ai_calls.

Behavior from specs/features/ai/ai-calls-log.md §2 and §4 (AC-1 to AC-16). The database writer
is a fake here; the real Supabase writer is covered by tests/integration (AC-17, AC-tenant).
"""

import asyncio
import json
import logging
import threading
import uuid
from pathlib import Path

import pytest
from pydantic import BaseModel, SecretStr

import app.ai.gateway as gateway_module
import app.settings as settings_module
from app.ai.call_context import AICallContext, ai_call_context, current_call_context
from app.ai.gateway import AIProviderError, CallRecord, Gateway
from app.ai.providers.base import EmbedRequest, EmbedResponse
from app.ai.providers.fake import FakeProvider
from app.db.ai_calls import AICallLog, SupabaseAICallsWriter, to_row
from app.settings import get_settings

REPO_PROMPTS: Path = get_settings().env.prompts_dir
TENANT = uuid.UUID("00000000-0000-4000-8000-000000000001")
USER = uuid.UUID("00000000-0000-4000-8000-000000000002")
SESSION = uuid.UUID("00000000-0000-4000-8000-000000000003")
REQUEST_ID = "6f1c2a4e-9b1d-4c3e-8f00-000000000004"

TOPICS_INPUT = {
    "file_name": "sheet-03.pdf",
    "material_kind": "exercise",
    "pages_text": "[p.1]\nจงหาลิมิตของฟังก์ชันลับ",
}
VALID_TOPICS = (
    '{"topics": [{"name": "ลิมิตลับเฉพาะ", "pages": ["2-6"], "prereq_hint": []}], "notes": ""}'
)
LOGGER = "app.ai.calls"


class Topic(BaseModel):
    name: str
    pages: list[str]
    prereq_hint: list[str]


class TopicsResult(BaseModel):
    topics: list[Topic]
    notes: str


class FakeWriter:
    """Keeps inserted rows. ``hold`` blocks every insert until the test sets it; ``fail``
    raises instead of inserting."""

    def __init__(self, hold: threading.Event | None = None, fail: bool = False) -> None:
        self.rows: list[dict] = []
        self.started = threading.Event()
        self._hold = hold
        self._fail = fail

    def insert(self, row: dict) -> None:
        self.started.set()
        if self._hold is not None:
            self._hold.wait()
        if self._fail:
            raise ConnectionError("db down")
        self.rows.append(row)


class FakeEmbedder:
    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        return EmbedResponse(vectors=[[1.0, 0.0] for _ in request.texts], tokens_in=3)


class FakeWithEmbed(FakeProvider):
    """Fake provider that also embeds, so one gateway serves call, stream and embed."""

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        return await FakeEmbedder().embed(request)


def make_gateway(provider: FakeProvider) -> Gateway:
    config = get_settings().ai
    # Fakes return short vectors: ignore the vector size of config/ai.yaml.
    config = config.model_copy(
        update={"embedding": config.embedding.model_copy(update={"dimensions": None})}
    )
    return Gateway(config=config, prompts_dir=REPO_PROMPTS, provider=provider)


def logged(gateway_provider: FakeProvider, writer: FakeWriter | None) -> tuple[Gateway, AICallLog]:
    gateway = make_gateway(gateway_provider)
    call_log = AICallLog(writer=writer)
    gateway.add_listener(call_log)
    return gateway, call_log


def record(**changes) -> CallRecord:
    values = {
        "purpose": "tutor_reply",
        "provider": "vertex",
        "model": "gemini-3.5-flash",
        "prompt_version": "v1",
        "status": "ok",
        "tokens_in": 812,
        "tokens_out": 164,
        "latency_ms": 3712.4,
        "schema_retries": 0,
    }
    return CallRecord(**(values | changes))


FULL_CONTEXT = AICallContext(tenant_id=TENANT, user_id=USER, session_id=SESSION)


def call_lines(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [r for r in caplog.records if r.name == LOGGER]


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retry waits of the gateway are skipped, so no test waits for real."""

    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)


# --- AC-1 to AC-6 · to_row ---------------------------------------------------------------------


def test_AI04_row_has_every_column_of_the_record():
    row = to_row(record(), FULL_CONTEXT, REQUEST_ID)

    assert row == {
        "tenant_id": str(TENANT),
        "user_id": str(USER),
        "session_id": str(SESSION),
        "request_id": REQUEST_ID,
        "purpose": "tutor_reply",
        "provider": "vertex",
        "model": "gemini-3.5-flash",
        "prompt_version": "v1",
        "tokens_in": 812,
        "tokens_out": 164,
        "cached_tokens": None,
        "latency_ms": 3712,
        "cost_usd": None,
        "status": "ok",
        "fallback_used": False,
    }


@pytest.mark.parametrize(("schema_retries", "status"), [(0, "ok"), (1, "schema_retry")])
def test_AI04_status_schema_retry_from_one_retry(schema_retries: int, status: str):
    row = to_row(record(schema_retries=schema_retries), FULL_CONTEXT, REQUEST_ID)

    assert row["status"] == status


@pytest.mark.parametrize("failed", ["schema_error", "provider_error"])
def test_AI04_failed_record_maps_to_error(failed: str):
    row = to_row(record(status=failed, schema_retries=2), FULL_CONTEXT, REQUEST_ID)

    assert row["status"] == "error"


def test_AI04_embed_has_null_prompt_version():
    row = to_row(record(purpose="embed", prompt_version="none"), FULL_CONTEXT, None)

    assert row["prompt_version"] is None


def test_AI04_latency_rounded_to_int():
    row = to_row(record(latency_ms=3712.6), FULL_CONTEXT, None)

    assert row["latency_ms"] == 3713
    assert isinstance(row["latency_ms"], int)


def test_AI04_missing_context_fields_are_null():
    row = to_row(record(), AICallContext(tenant_id=TENANT), None)

    assert row["tenant_id"] == str(TENANT)
    assert row["user_id"] is None
    assert row["session_id"] is None
    assert row["request_id"] is None


# --- AC-7 · call context ----------------------------------------------------------------------


def test_AI04_call_context_nests_and_resets():
    assert current_call_context() is None

    with ai_call_context(tenant_id=TENANT):
        assert current_call_context() == AICallContext(tenant_id=TENANT)
        with ai_call_context(tenant_id=TENANT, session_id=SESSION):
            assert current_call_context() == AICallContext(tenant_id=TENANT, session_id=SESSION)
        assert current_call_context().session_id is None

    assert current_call_context() is None


# --- AC-8 to AC-14 · listener with the gateway -------------------------------------------------


async def test_AI04_call_writes_one_row_with_tenant():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})
    writer = FakeWriter()
    gateway, call_log = logged(fake, writer)

    with ai_call_context(tenant_id=TENANT, user_id=USER):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    await call_log.flush()

    assert len(writer.rows) == 1
    row = writer.rows[0]
    assert row["tenant_id"] == str(TENANT)
    assert row["user_id"] == str(USER)
    assert row["purpose"] == "extract_topics_local"
    assert row["tokens_in"] == sum(r.tokens_in for r in fake.responses_sent)
    assert row["tokens_out"] == sum(r.tokens_out for r in fake.responses_sent)


async def test_AI04_stream_and_embed_write_one_row_each():
    fake = FakeWithEmbed({"tutor_reply": ["สวัสดีครับ วันนี้ทวนลิมิตกัน"]})
    writer = FakeWriter()
    gateway, call_log = logged(fake, writer)

    with ai_call_context(tenant_id=TENANT, session_id=SESSION):
        chunks = [chunk async for chunk in gateway.stream("tutor_reply", {"message": "สวัสดี"})]
        await gateway.embed(["ลิมิต"], role="query")
    await call_log.flush()

    assert chunks
    assert [(r["purpose"], r["status"]) for r in writer.rows] == [
        ("tutor_reply", "ok"),
        ("embed", "ok"),
    ]
    assert all(r["session_id"] == str(SESSION) for r in writer.rows)


async def test_AI04_failed_call_still_writes_error_row():
    retries = get_settings().ai.gateway.retries
    fake = FakeProvider({"extract_topics_local": [RuntimeError("503")] * (retries + 1)})
    writer = FakeWriter()
    gateway, call_log = logged(fake, writer)

    with ai_call_context(tenant_id=TENANT), pytest.raises(AIProviderError):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    await call_log.flush()

    assert [r["status"] for r in writer.rows] == ["error"]


async def test_AI04_no_tenant_logs_but_does_not_write(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger=LOGGER)
    writer = FakeWriter()
    gateway, call_log = logged(FakeProvider({"extract_topics_local": [VALID_TOPICS]}), writer)

    await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    await call_log.flush()

    assert writer.rows == []
    lines = call_lines(caplog)
    assert len(lines) == 1
    assert lines[0].levelno == logging.INFO
    line = json.loads(lines[0].getMessage())
    assert line["tenant_id"] is None
    assert line["purpose"] == "extract_topics_local"


async def test_AI04_log_line_is_json_without_prompt_text(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO, logger=LOGGER)
    writer = FakeWriter()
    gateway, call_log = logged(FakeProvider({"extract_topics_local": [VALID_TOPICS]}), writer)

    with ai_call_context(tenant_id=TENANT):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    await call_log.flush()

    assert len(writer.rows) == 1
    lines = call_lines(caplog)
    assert len(lines) == 1
    message = lines[0].getMessage()
    line = json.loads(message)
    assert line["tenant_id"] == str(TENANT)
    assert line["schema_retries"] == 0
    assert "จงหาลิมิตของฟังก์ชันลับ" not in message  # prompt input
    assert "ลิมิตลับเฉพาะ" not in message  # model answer


async def test_AI04_call_does_not_wait_for_the_writer():
    hold = threading.Event()
    writer = FakeWriter(hold=hold)
    gateway, call_log = logged(FakeProvider({"extract_topics_local": [VALID_TOPICS]}), writer)

    try:
        with ai_call_context(tenant_id=TENANT):
            result = await asyncio.wait_for(
                gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult), timeout=5
            )
        assert len(result.topics) == 1
        assert writer.rows == []  # the insert is still held
    finally:
        hold.set()
    await call_log.flush()

    assert len(writer.rows) == 1


async def test_AI04_writer_failure_only_warns(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.INFO)
    writer = FakeWriter(fail=True)
    gateway, call_log = logged(FakeProvider({"extract_topics_local": [VALID_TOPICS]}), writer)

    with ai_call_context(tenant_id=TENANT):
        result = await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    await call_log.flush()  # must not raise the writer's error

    assert len(result.topics) == 1
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "extract_topics_local" in warnings[0].getMessage()


# --- AC-15, AC-16 · build_default_gateway() ---------------------------------------------------


def use_env(monkeypatch: pytest.MonkeyPatch, *, supabase_url: str = "", service_key: str = ""):
    """build_default_gateway() in fake mode reads these settings instead of the .env."""
    settings = get_settings()
    env = settings.env.model_copy(
        update={
            "ai_provider": "fake",
            "ai_model_override": "",
            "supabase_url": supabase_url,
            "supabase_service_role_key": SecretStr(service_key),
        }
    )
    changed = settings.model_copy(update={"env": env})
    monkeypatch.setattr(settings_module, "get_settings", lambda: changed)


def call_logs(gateway: Gateway) -> list[AICallLog]:
    return [listener for listener in gateway._listeners if isinstance(listener, AICallLog)]


def test_AI04_default_gateway_logs_without_supabase(monkeypatch: pytest.MonkeyPatch):
    use_env(monkeypatch)

    gateway = gateway_module.build_default_gateway()

    logs = call_logs(gateway)
    assert len(logs) == 1
    assert logs[0].writer is None


@pytest.mark.parametrize(
    ("supabase_url", "service_key"),
    [("http://127.0.0.1:54321", ""), ("", "service-role-key")],
)
def test_AI04_default_gateway_needs_both_supabase_values(
    monkeypatch: pytest.MonkeyPatch, supabase_url: str, service_key: str
):
    use_env(monkeypatch, supabase_url=supabase_url, service_key=service_key)

    gateway = gateway_module.build_default_gateway()

    assert call_logs(gateway)[0].writer is None


def test_AI04_default_gateway_writes_with_supabase_env(monkeypatch: pytest.MonkeyPatch):
    use_env(monkeypatch, supabase_url="http://127.0.0.1:54321", service_key="service-role-key")

    gateway = gateway_module.build_default_gateway()

    logs = call_logs(gateway)
    assert len(logs) == 1
    assert isinstance(logs[0].writer, SupabaseAICallsWriter)
