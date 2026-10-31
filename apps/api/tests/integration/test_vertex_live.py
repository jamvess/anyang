"""Smoke test on real Vertex AI (specs/features/ai/gemini-vertex.md AC-16). Marked ``live``, so
pytest and CI skip it unless run with ``-m live``. Needs ADC (``gcloud auth
application-default login``) and GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION in .env."""

import time

import pytest
from pydantic import BaseModel

from app.ai.gateway import CallRecord, Gateway
from app.ai.providers.gemini import GeminiProvider
from app.settings import get_settings

pytestmark = pytest.mark.live


class Topic(BaseModel):
    name: str
    pages: list[str]
    prereq_hint: list[str]


class TopicsResult(BaseModel):
    topics: list[Topic]
    notes: str


async def test_AI01_vertex_answers_a_tier_mid_call_from_config():
    settings = get_settings()
    env = settings.env
    if not env.google_cloud_project:
        pytest.skip("GOOGLE_CLOUD_PROJECT is not set")
    provider = GeminiProvider.vertex(
        project=env.google_cloud_project, location=env.google_cloud_location
    )
    records: list[CallRecord] = []
    gateway = Gateway.live(settings.ai, env.prompts_dir, providers={"vertex": provider})
    gateway.add_listener(records.append)

    result = await gateway.call(
        "extract_topics_local",
        {
            "file_name": "sheet-03.pdf",
            "material_kind": "exercise",
            "pages_text": "[p.1]\n" + r"จงหาลิมิต $\lim_{x \to 2} \frac{x^2-4}{x-2}$",
        },
        TopicsResult,
    )

    record = records[-1]
    print(
        f"\nvertex smoke: model={record.model} location={env.google_cloud_location} "
        f"tokens_in={record.tokens_in} tokens_out={record.tokens_out} "
        f"latency_ms={record.latency_ms:.0f}"
    )
    assert result.topics
    assert record.provider == "vertex"
    assert record.tokens_in > 0


async def test_AI01_vertex_streams_tutor_reply():
    # specs/features/tutor/tutor-reply-stream.md §8 live smoke · prints TTFT for P4-lite
    settings = get_settings()
    env = settings.env
    if not env.google_cloud_project:
        pytest.skip("GOOGLE_CLOUD_PROJECT is not set")
    provider = GeminiProvider.vertex(
        project=env.google_cloud_project, location=env.google_cloud_location
    )
    records: list[CallRecord] = []
    gateway = Gateway.live(settings.ai, env.prompts_dir, providers={"vertex": provider})
    gateway.add_listener(records.append)

    started = time.perf_counter()
    first_token_ms: float | None = None
    chunks: list[str] = []
    async for chunk in gateway.stream("tutor_reply", {"message": "แยกตัวประกอบ $x^2-49$ ยังไง"}):
        if first_token_ms is None:
            first_token_ms = (time.perf_counter() - started) * 1000
        chunks.append(chunk)

    record = records[-1]
    print(
        f"\nvertex stream: model={record.model} chunks={len(chunks)} "
        f"ttft_ms={first_token_ms:.0f} total_ms={record.latency_ms:.0f} "
        f"tokens_in={record.tokens_in} tokens_out={record.tokens_out}\n{''.join(chunks)}"
    )
    assert chunks
    assert record.status == "ok"
