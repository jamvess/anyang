"""A cut answer in ai_calls and its log line (specs/features/ai/gateway-truncation.md §2.4 ·
AC-11, AC-12). test_ai_calls_log.py stays as it was reviewed."""

import json
import logging

import pytest

import app.ai.gateway as gateway_module
from app.ai.call_context import ai_call_context
from app.ai.gateway import AITruncatedError
from app.ai.providers.fake import FakeProvider, Truncated
from app.db.ai_calls import to_row
from app.models.scope_ai import ClassifyMaterialResult
from tests.unit.test_ai_calls_log import (
    LOGGER,
    TENANT,
    FakeWriter,
    call_lines,
    logged,
    record,
)

PURPOSE = "classify_material"
INPUT = {"file_name": "sheet-03.pdf", "pages_text": "[p.1]\nลิมิต", "user_note": "ไม่มี"}
VALID = '{"kind": "sheet", "confidence": 0.9, "other_instructor": false, "reason": "ชีท"}'


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)


# --- AC-11 · to_row ---------------------------------------------------------------------------


@pytest.mark.parametrize("schema_retries", [0, 1])
def test_AI04_truncated_record_maps_to_error(schema_retries: int):
    row = to_row(record(status="truncated", schema_retries=schema_retries), None, None)

    assert row["status"] == "error"


# --- AC-12 · the log line ---------------------------------------------------------------------


async def test_AI04_log_line_tells_a_cut_answer_from_a_schema_error(
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.INFO, logger=LOGGER)
    writer = FakeWriter()
    gateway, call_log = logged(FakeProvider({PURPOSE: [Truncated('{"kind": "sh'), VALID]}), writer)

    with ai_call_context(tenant_id=TENANT):
        with pytest.raises(AITruncatedError):
            await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)
        await gateway.call(PURPOSE, INPUT, ClassifyMaterialResult)
    await call_log.flush()

    lines = [json.loads(r.getMessage()) for r in call_lines(caplog)]
    assert [(line["status"], line["call_status"]) for line in lines] == [
        ("error", "truncated"),
        ("ok", "ok"),
    ]
    assert [row["status"] for row in writer.rows] == ["error", "ok"]
    assert all("call_status" not in row for row in writer.rows)  # the table is unchanged
