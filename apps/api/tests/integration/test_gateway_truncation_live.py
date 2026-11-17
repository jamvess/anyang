"""A cut answer on real Vertex AI is not retried (specs/features/ai/gateway-truncation.md AC-14).
Marked ``live``, so pytest and CI skip it unless run with ``-m live``. Needs ADC (``gcloud auth
application-default login``) and GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION in .env.
config/ai.yaml is not changed: the small max_tokens lives in this test's copy of the config."""

import pytest

from app.ai.gateway import AITruncatedError, CallRecord, Gateway
from app.ai.providers.gemini import GeminiProvider
from app.models.scope_ai import ClassifyMaterialResult
from app.settings import get_settings

pytestmark = pytest.mark.live

PURPOSE = "classify_material"
TINY_MAX_TOKENS = 16  # far below one JSON answer of classify_material


async def test_AI01_vertex_cut_answer_is_not_retried():
    settings = get_settings()
    env = settings.env
    if not env.google_cloud_project:
        pytest.skip("GOOGLE_CLOUD_PROJECT is not set")
    provider = GeminiProvider.vertex(
        project=env.google_cloud_project, location=env.google_cloud_location
    )
    purposes = dict(settings.ai.purposes)
    purposes[PURPOSE] = purposes[PURPOSE].model_copy(update={"max_tokens": TINY_MAX_TOKENS})
    config = settings.ai.model_copy(update={"purposes": purposes})
    records: list[CallRecord] = []
    gateway = Gateway.live(config, env.prompts_dir, providers={"vertex": provider})
    gateway.add_listener(records.append)

    with pytest.raises(AITruncatedError):
        await gateway.call(
            PURPOSE,
            {
                "file_name": "sheet-03.pdf",
                "pages_text": "[p.1]\nเอกสารประกอบการเรียน MTH10101 บทที่ 3 ลิมิตและความต่อเนื่อง",
                "user_note": "ไม่มี",
            },
            ClassifyMaterialResult,
        )

    assert len(records) == 1
    record = records[0]
    print(
        f"\nvertex cut: model={record.model} tokens_in={record.tokens_in} "
        f"tokens_out={record.tokens_out} latency_ms={record.latency_ms:.0f}"
    )
    assert record.status == "truncated"
    assert record.schema_retries == 0
