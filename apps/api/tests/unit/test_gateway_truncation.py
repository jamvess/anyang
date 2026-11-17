"""The gateway does not retry an answer the provider cut at max_tokens
(specs/features/ai/gateway-truncation.md §2.1 to §2.4 · AC-3 to AC-10, AC-13). Fake provider only
(AI-03). Retry counts and breaker thresholds come from config/ai.yaml, never literals."""

import logging

import pytest

import app.ai.gateway as gateway_module
from app.ai.gateway import AISchemaError, AITruncatedError, CallRecord, Gateway
from app.ai.providers.base import ProviderRequest
from app.ai.providers.fake import FakeProvider, Truncated
from app.models.scope_ai import ClassifyMaterialResult
from app.settings import get_settings
from tests.unit.test_ai_gateway import REPO_PROMPTS

PURPOSE = "classify_material"
INPUT = {"file_name": "sheet-03.pdf", "pages_text": "[p.1]\nลิมิต", "user_note": "ไม่มี"}
VALID = '{"kind": "sheet", "confidence": 0.9, "other_instructor": false, "reason": "ชีท"}'
CUT = '{"kind": "sh'
CONFIG = get_settings().ai
MAX_TOKENS = CONFIG.purposes[PURPOSE].max_tokens


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)


def make_gateway(fake: FakeProvider) -> tuple[Gateway, list[CallRecord]]:
    gateway = Gateway(config=CONFIG, prompts_dir=REPO_PROMPTS, provider=fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)
    return gateway, records


def calls_of(fake: FakeProvider, purpose: str = PURPOSE) -> list[ProviderRequest]:
    return [r for r in fake.requests if r.purpose == purpose]


# --- AC-3 · fake provider ---------------------------------------------------------------------


async def test_AI03_fake_scripts_a_truncated_answer():
    fake = FakeProvider({PURPOSE: [Truncated(CUT), VALID]})
    request = ProviderRequest(
        purpose=PURPOSE, model="m", prompt="x", temperature=0.0, max_tokens=MAX_TOKENS
    )

    cut = await fake.generate(request)
    whole = await fake.generate(request)

    assert (cut.text, cut.truncated) == (CUT, True)
    assert (whole.text, whole.truncated) == (VALID, False)


# --- AC-4, AC-8 · cut and invalid: no retry ---------------------------------------------------


async def test_AI01_cut_answer_is_not_retried_and_raises_a_schema_error():
    fake = FakeProvider({PURPOSE: [Truncated(CUT), VALID]})
    gateway, _ = make_gateway(fake)

    with pytest.raises(AITruncatedError) as raised:
        await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)

    assert isinstance(raised.value, AISchemaError)  # AC-9: callers that catch it need no change
    assert len(calls_of(fake)) == 1
    assert PURPOSE in str(raised.value)
    assert "max_tokens" in str(raised.value)


async def test_AI04_cut_answer_gives_one_truncated_record():
    fake = FakeProvider({PURPOSE: [Truncated(CUT)]})
    gateway, records = make_gateway(fake)

    with pytest.raises(AITruncatedError):
        await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)

    assert len(records) == 1
    assert records[0].status == "truncated"
    assert records[0].schema_retries == 0
    assert records[0].tokens_out == fake.responses_sent[0].tokens_out


# --- AC-5 · cut but whole -------------------------------------------------------------------


async def test_AI01_cut_answer_that_parses_is_used():
    fake = FakeProvider({PURPOSE: [Truncated(VALID)]})
    gateway, records = make_gateway(fake)

    result = await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)

    assert result.kind == "sheet"
    assert records[0].status == "ok"


# --- AC-6, AC-7 · schema retry -------------------------------------------------------------


async def test_AI01_answer_off_the_schema_without_a_cut_is_still_retried():
    fake = FakeProvider({PURPOSE: ["not json", VALID]})
    gateway, records = make_gateway(fake)

    result = await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)

    assert result.kind == "sheet"
    assert len(calls_of(fake)) == 2
    assert records[0].status == "ok"


@pytest.mark.skipif(CONFIG.gateway.schema_retries < 1, reason="needs one schema retry in config")
async def test_AI01_cut_answer_in_the_retry_stops_there():
    retries = CONFIG.gateway.schema_retries
    fake = FakeProvider({PURPOSE: ["not json"] * retries + [Truncated(CUT)]})
    gateway, records = make_gateway(fake)

    with pytest.raises(AITruncatedError):
        await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)

    assert len(calls_of(fake)) == retries + 1
    assert records[0].status == "truncated"
    assert records[0].schema_retries == retries


# --- AC-10 · stream -------------------------------------------------------------------------


async def test_AI04_cut_stream_keeps_its_chunks_and_is_logged(caplog: pytest.LogCaptureFixture):
    caplog.set_level(logging.WARNING, logger="app.ai.gateway")
    fake = FakeProvider({"tutor_reply": [Truncated("ลองแยก ตัวประกอบ ดู")]})
    gateway, records = make_gateway(fake)

    chunks = [c async for c in gateway.stream("tutor_reply", {"message": "ทำยังไง"})]

    assert "".join(chunks) == "ลองแยก ตัวประกอบ ดู"
    assert records[0].status == "truncated"
    warnings = [
        r for r in caplog.records if r.name == "app.ai.gateway" and r.levelno == logging.WARNING
    ]
    assert len(warnings) == 1
    assert "tutor_reply" in warnings[0].getMessage()


async def test_AI04_stream_that_ends_normally_is_ok():
    fake = FakeProvider({"tutor_reply": ["ลองแยก ตัวประกอบ ดู"]})
    gateway, records = make_gateway(fake)

    chunks = [c async for c in gateway.stream("tutor_reply", {"message": "ทำยังไง"})]

    assert "".join(chunks) == "ลองแยก ตัวประกอบ ดู"
    assert records[0].status == "ok"


# --- AC-13 · circuit breaker ----------------------------------------------------------------


async def test_NFRR1_cut_answers_do_not_open_the_breaker():
    cb = CONFIG.gateway.circuit_breaker
    fake = FakeProvider({PURPOSE: [Truncated(CUT)] * cb.minimum_calls})
    gateway, _ = make_gateway(fake)

    for _ in range(cb.minimum_calls):
        with pytest.raises(AITruncatedError):
            await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)

    assert gateway.breaker("fake").state == "closed"
