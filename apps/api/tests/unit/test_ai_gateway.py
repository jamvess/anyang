"""AI gateway lite: ai.call(purpose, input, schema).

Behavior from specs/requirements/requirements.md AI-01..AI-05, ai-orchestration.md §2.9-2.11
and prompts/README.md. Lite scope (PoC P3): no fallback provider, no circuit breaker, and the
call record goes to listeners instead of the ai_calls table (Junior's S3 work).
"""

import asyncio
from pathlib import Path

import pytest
from pydantic import BaseModel

from app.ai.gateway import (
    AIConfigError,
    AIInputError,
    AIProviderError,
    AISchemaError,
    CallRecord,
    Gateway,
    Image,
)
from app.ai.providers.base import ProviderRequest, ProviderResponse
from app.ai.providers.fake import FakeProvider
from app.settings import get_settings

REPO_PROMPTS = get_settings().env.prompts_dir
VALID_TOPICS = (
    '{"topics": [{"name": "ลิมิต (Limit)", "pages": ["2-6"], "prereq_hint": []}], "notes": ""}'
)
TOPICS_INPUT = {
    "file_name": "sheet-03.pdf",
    "material_kind": "exercise",
    "pages_text": "[p.1]\nจงหา",
}


class Topic(BaseModel):
    name: str
    pages: list[str]
    prereq_hint: list[str]


class TopicsResult(BaseModel):
    topics: list[Topic]
    notes: str


class AnswerLine(BaseModel):
    latex: str
    confidence: float


class AnswerResult(BaseModel):
    lines: list[AnswerLine]
    notes: str


def make_gateway(fake: FakeProvider, prompts_dir: Path = REPO_PROMPTS, **config_changes) -> Gateway:
    config = get_settings().ai
    if config_changes:
        config = config.model_copy(update=config_changes)
    return Gateway(config=config, prompts_dir=prompts_dir, provider=fake)


def write_prompt(
    root: Path, purpose: str, body: str, inputs: str, frontmatter_purpose: str = ""
) -> None:
    folder = root / purpose
    folder.mkdir(parents=True)
    (folder / "v1.md").write_text(
        f"---\npurpose: {frontmatter_purpose or purpose}\nversion: 1\n"
        f"output_schema: X\ninputs: [{inputs}]\n---\n\n{body}\n",
        encoding="utf-8",
    )


# --- AI-03 fake provider ------------------------------------------------------------------


async def test_AI03_fake_provider_returns_scripted_output():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})

    result = await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert result == TopicsResult.model_validate_json(VALID_TOPICS)
    assert len(fake.requests) == 1


async def test_AI03_fake_provider_without_script_fails_loudly():
    with pytest.raises(AIProviderError, match="no scripted response"):
        await make_gateway(FakeProvider({})).call(
            "extract_topics_local", TOPICS_INPUT, TopicsResult
        )


# --- AI-01 prompts and inputs ---------------------------------------------------------------


async def test_AI01_prompt_is_rendered_from_prompts_dir():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})

    await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    prompt = fake.requests[0].prompt
    assert '<document name="sheet-03.pdf">' in prompt
    assert "[p.1]\nจงหา" in prompt
    assert "{{" not in prompt
    assert not prompt.startswith("---")  # frontmatter is not sent to the model


async def test_AI01_missing_input_is_rejected_before_calling_the_model():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})
    incomplete = {k: v for k, v in TOPICS_INPUT.items() if k != "pages_text"}

    with pytest.raises(AIInputError, match="pages_text"):
        await make_gateway(fake).call("extract_topics_local", incomplete, TopicsResult)
    assert fake.requests == []


async def test_AI01_unknown_input_is_rejected():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})

    with pytest.raises(AIInputError, match="persona"):
        await make_gateway(fake).call(
            "extract_topics_local", TOPICS_INPUT | {"persona": "x"}, TopicsResult
        )


async def test_AI01_image_input_is_sent_as_attachment_not_text():
    fake = FakeProvider({"extract_answer": ['{"lines": [], "notes": ""}']})
    photo = Image(data=b"\xff\xd8 jpeg bytes", mime_type="image/jpeg")

    await make_gateway(fake).call(
        "extract_answer", {"image": photo, "problem_text": "x^{2}-1"}, AnswerResult
    )

    request = fake.requests[0]
    assert request.images == [photo]
    assert "<problem>x^{2}-1</problem>" in request.prompt


async def test_AI01_placeholder_without_declared_input_is_rejected(tmp_path: Path):
    write_prompt(tmp_path, "demo", "Hello {{name}} and {{other}}", inputs="name")
    fake = FakeProvider({"demo": ['{"notes": ""}']})
    config = get_settings().ai
    purposes = config.purposes | {"demo": config.purposes["route_intent"]}

    with pytest.raises(AIInputError, match="other"):
        await make_gateway(fake, tmp_path, purposes=purposes).call(
            "demo", {"name": "Jam"}, BaseModel
        )


async def test_AI01_frontmatter_purpose_must_match(tmp_path: Path):
    write_prompt(tmp_path, "demo", "Hi {{name}}", inputs="name", frontmatter_purpose="other")
    config = get_settings().ai
    purposes = config.purposes | {"demo": config.purposes["route_intent"]}

    with pytest.raises(AIConfigError, match="purpose"):
        await make_gateway(FakeProvider({}), tmp_path, purposes=purposes).call(
            "demo", {"name": "Jam"}, BaseModel
        )


async def test_AI01_unknown_purpose_is_rejected():
    with pytest.raises(AIConfigError, match="not_a_purpose"):
        await make_gateway(FakeProvider({})).call("not_a_purpose", {}, BaseModel)


# --- AI-02 routing from config/ai.yaml --------------------------------------------------------


async def test_AI02_model_and_parameters_come_from_config():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})
    config = get_settings().ai
    purpose = config.purposes["extract_topics_local"]

    await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    request = fake.requests[0]
    assert request.model == config.tiers[purpose.tier].primary
    assert request.temperature == purpose.temperature
    assert request.max_tokens == purpose.max_tokens


@pytest.mark.parametrize("level", ["low", "medium", "high", None])
async def test_AI02_thinking_level_comes_from_config(level):
    # Gemini 3 counts thinking tokens inside max_tokens; transcription purposes set "low".
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})
    config = get_settings().ai
    purposes = config.purposes | {
        "extract_topics_local": config.purposes["extract_topics_local"].model_copy(
            update={"thinking": level}
        )
    }

    await make_gateway(fake, purposes=purposes).call(
        "extract_topics_local", TOPICS_INPUT, TopicsResult
    )

    assert fake.requests[0].thinking == level


def test_AI02_thinking_level_must_be_known():
    from pydantic import ValidationError

    from app.settings import PurposeConfig

    with pytest.raises(ValidationError):
        PurposeConfig(
            tier="mid", temperature=0, max_tokens=10, timeout_s=1, prompt="v1", thinking="max"
        )


async def test_AI02_model_override_replaces_the_tier_model():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})
    gateway = Gateway(
        config=get_settings().ai,
        prompts_dir=REPO_PROMPTS,
        provider=fake,
        model_override="gemini:gemini-test-flash",
    )

    await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert fake.requests[0].model == "gemini:gemini-test-flash"


async def test_AI02_live_mode_refuses_placeholder_model_ids():
    # config/ai.yaml keeps "TODO-..." model ids until the PoC spikes choose real ones.
    gateway = Gateway.live(config=get_settings().ai, prompts_dir=REPO_PROMPTS, providers={})

    with pytest.raises(AIConfigError, match="TODO"):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)


async def test_AI02_live_mode_picks_provider_by_model_prefix():
    seen: list[ProviderRequest] = []

    class Recorder:
        async def generate(self, request: ProviderRequest) -> ProviderResponse:
            seen.append(request)
            return ProviderResponse(text=VALID_TOPICS, tokens_in=10, tokens_out=5)

    gateway = Gateway.live(
        config=get_settings().ai,
        prompts_dir=REPO_PROMPTS,
        providers={"gemini": Recorder()},
        model_override="gemini:gemini-test-flash",
    )

    await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert seen[0].model == "gemini-test-flash"  # prefix removed before the provider sees it


# --- AI-05 schema validation and retry -------------------------------------------------------


async def test_AI05_invalid_output_is_retried_with_the_error_message():
    fake = FakeProvider({"extract_topics_local": ["not json at all", VALID_TOPICS]})

    result = await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert result.topics[0].name == "ลิมิต (Limit)"
    assert len(fake.requests) == 2
    retry_prompt = fake.requests[1].prompt
    assert retry_prompt.startswith(fake.requests[0].prompt)
    assert "did not match the schema" in retry_prompt


async def test_AI05_gives_up_after_schema_retries_from_config():
    retries = get_settings().ai.gateway.schema_retries
    fake = FakeProvider({"extract_topics_local": ['{"topics": "wrong"}'] * (retries + 1)})

    with pytest.raises(AISchemaError):
        await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    assert len(fake.requests) == retries + 1


async def test_AI05_markdown_code_fence_is_accepted():
    fenced = f"```json\n{VALID_TOPICS}\n```"
    fake = FakeProvider({"extract_topics_local": [fenced]})

    result = await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert len(result.topics) == 1


# --- ai-orchestration.md §2.10 provider errors and timeout -------------------------------------


async def test_ai_orchestration_2_10_provider_error_is_retried_from_config():
    retries = get_settings().ai.gateway.retries
    failures: list = [RuntimeError("503")] * retries
    fake = FakeProvider({"extract_topics_local": [*failures, VALID_TOPICS]})

    result = await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert len(result.topics) == 1


async def test_ai_orchestration_2_10_provider_error_after_retries_raises():
    retries = get_settings().ai.gateway.retries
    fake = FakeProvider({"extract_topics_local": [RuntimeError("503")] * (retries + 1)})

    with pytest.raises(AIProviderError, match="503"):
        await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)


async def test_ai_orchestration_2_10_timeout_from_config_counts_as_provider_error():
    config = get_settings().ai
    purposes = config.purposes | {
        "extract_topics_local": config.purposes["extract_topics_local"].model_copy(
            update={"timeout_s": 0.01}
        )
    }
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS] * 5}, delay_s=0.2)
    gateway = make_gateway(
        fake, purposes=purposes, gateway=config.gateway.model_copy(update={"retries": 0})
    )

    with pytest.raises(AIProviderError, match="timeout"):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)


# --- AI-04 call record ------------------------------------------------------------------------


async def test_AI04_every_call_produces_a_record_with_tokens():
    fake = FakeProvider({"extract_topics_local": ["oops", VALID_TOPICS]})
    gateway = make_gateway(fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)

    await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert len(records) == 1
    record = records[0]
    assert record.purpose == "extract_topics_local"
    assert record.prompt_version == "v1"
    assert record.status == "ok"
    assert record.schema_retries == 1
    assert record.tokens_in == sum(r.tokens_in for r in fake.responses_sent)
    assert record.tokens_out == sum(r.tokens_out for r in fake.responses_sent)
    assert record.latency_ms >= 0


async def test_AI04_failed_call_is_recorded_too():
    fake = FakeProvider({"extract_topics_local": ["bad"] * 5})
    gateway = make_gateway(fake)
    records: list[CallRecord] = []
    gateway.add_listener(records.append)

    with pytest.raises(AISchemaError):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert [r.status for r in records] == ["schema_error"]


def test_AI04_listener_errors_do_not_break_the_call():
    fake = FakeProvider({"extract_topics_local": [VALID_TOPICS]})
    gateway = make_gateway(fake)

    def broken(record: CallRecord) -> None:
        raise ValueError("log sink down")

    gateway.add_listener(broken)

    result = asyncio.run(gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult))
    assert len(result.topics) == 1


# --- AI-01 several images in one input (PoC P3: a whole scanned exam in one call) -----------


async def test_AI01_list_of_images_is_sent_as_attachments_in_order(tmp_path: Path):
    write_prompt(tmp_path, "demo", "Read {{file_name}}", inputs="images, file_name")
    fake = FakeProvider({"demo": ['{"notes": ""}']})
    config = get_settings().ai
    purposes = config.purposes | {"demo": config.purposes["route_intent"]}
    pages = [Image(data=bytes([n]), mime_type="image/png") for n in range(3)]

    await make_gateway(fake, tmp_path, purposes=purposes).call(
        "demo", {"images": pages, "file_name": "exam.pdf"}, BaseModel
    )

    assert fake.requests[0].images == pages
    assert fake.requests[0].prompt == "Read exam.pdf"


async def test_AI01_list_input_must_contain_only_images(tmp_path: Path):
    write_prompt(tmp_path, "demo", "Read {{file_name}}", inputs="images, file_name")
    config = get_settings().ai
    purposes = config.purposes | {"demo": config.purposes["route_intent"]}

    with pytest.raises(AIInputError, match="images"):
        await make_gateway(FakeProvider({}), tmp_path, purposes=purposes).call(
            "demo", {"images": ["not an image"], "file_name": "exam.pdf"}, BaseModel
        )
