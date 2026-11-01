"""AI gateway lite: ai.call(purpose, input, schema).

Behavior from specs/requirements/requirements.md AI-01..AI-05, ai-orchestration.md §2.9-2.11
and prompts/README.md. Lite scope (PoC P3): no fallback provider, no circuit breaker, and the
call record goes to listeners instead of the ai_calls table (Junior's S3 work).
"""

import asyncio
from pathlib import Path

import pytest
from pydantic import BaseModel, SecretStr

import app.ai.gateway as gateway_module
import app.ai.providers.gemini as gemini_module
import app.settings as settings_module
from app.ai.gateway import (
    AIConfigError,
    AIInputError,
    AIProviderError,
    AISchemaError,
    CallRecord,
    Gateway,
    Image,
)
from app.ai.latex import LatexStr, MathTextStr
from app.ai.providers.base import (
    EmbedRequest,
    EmbedResponse,
    ProviderRateLimited,
    ProviderRequest,
    ProviderResponse,
)
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
    latex: LatexStr  # opt-in LaTeX repair (review of PR #15); was str
    confidence: float


class AnswerResult(BaseModel):
    lines: list[AnswerLine]
    notes: str


def make_gateway(fake: FakeProvider, prompts_dir: Path = REPO_PROMPTS, **config_changes) -> Gateway:
    config = get_settings().ai
    # Fakes return short vectors: ignore the vector size of config/ai.yaml unless a test sets it.
    config = config.model_copy(
        update={"embedding": config.embedding.model_copy(update={"dimensions": None})}
    )
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


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retry waits are recorded instead of slept, so no test waits for real."""
    recorded: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(gateway_module, "_sleep", fake_sleep)
    return recorded


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
    # A tier whose model id is still "TODO-..." must be refused in live mode.
    config = get_settings().ai
    mid = config.tiers["mid"].model_copy(update={"primary": "vertex:TODO-gemini-mid"})
    config = config.model_copy(update={"tiers": {**config.tiers, "mid": mid}})
    gateway = Gateway.live(config=config, prompts_dir=REPO_PROMPTS, providers={})

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
    # Version from config/ai.yaml, not a literal (Jam ok 2026-10-31: v2 since P3a on Vertex).
    assert record.prompt_version == get_settings().ai.purposes["extract_topics_local"].prompt
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


class NotesOnly(BaseModel):
    notes: str


async def test_AI01_list_of_images_is_sent_as_attachments_in_order(tmp_path: Path):
    write_prompt(tmp_path, "demo", "Read {{file_name}}", inputs="images, file_name")
    fake = FakeProvider({"demo": ['{"notes": ""}']})
    config = get_settings().ai
    purposes = config.purposes | {"demo": config.purposes["route_intent"]}
    pages = [Image(data=bytes([n]), mime_type="image/png") for n in range(3)]

    await make_gateway(fake, tmp_path, purposes=purposes).call(
        "demo", {"images": pages, "file_name": "exam.pdf"}, NotesOnly
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


# --- AI-05 LaTeX backslashes the model forgot to escape in JSON (found in PoC P1) -----------
# A model writes "\frac" inside a JSON string. JSON reads "\f" as a form feed, so the LaTeX
# silently becomes form feed + "rac" and still passes the schema. Fields typed LatexStr put it
# back; other fields are left alone (review of PR #15).


async def call_extract_answer(raw: str) -> tuple[AnswerResult, FakeProvider]:
    fake = FakeProvider({"extract_answer": [raw]})
    photo = Image(data=b"\xff\xd8 jpeg bytes", mime_type="image/jpeg")
    result = await make_gateway(fake).call(
        "extract_answer", {"image": photo, "problem_text": "x"}, AnswerResult
    )
    return result, fake


def answer_json(*latex: str, notes: str = "") -> str:
    """The model's raw text, with each backslash exactly as the model wrote it."""
    lines = ", ".join(f'{{"latex": "{line}", "confidence": 0.9}}' for line in latex)
    return f'{{"lines": [{lines}], "notes": "{notes}"}}'


async def test_AI05_form_feed_and_backspace_become_latex_commands():
    result, fake = await call_extract_answer(answer_json(r"\frac{1}{x}", r"\beta+\bar{x}"))

    assert [line.latex for line in result.lines] == [r"\frac{1}{x}", r"\beta+\bar{x}"]
    assert len(fake.requests) == 1  # repaired before validation, no schema retry spent


async def test_AI05_tab_or_carriage_return_before_a_letter_becomes_latex_command():
    # "\l" is not a JSON escape, so the model escaped \left correctly but not \right.
    result, _ = await call_extract_answer(answer_json(r"\theta\times\tan(x)", r"\\left(x\right)"))

    assert [line.latex for line in result.lines] == [r"\theta\times\tan(x)", r"\left(x\right)"]


async def test_AI05_newline_before_a_latex_command_name_becomes_latex_command():
    result, _ = await call_extract_answer(answer_json(r"x\neq 0", r"\nabla f", r"x\notin A"))

    assert [line.latex for line in result.lines] == [r"x\neq 0", r"\nabla f", r"x\notin A"]


async def test_AI05_ordinary_newline_and_tab_are_kept():
    notes = r"line one\nline two\nother\tค่า"
    result, _ = await call_extract_answer(answer_json("x", notes=notes))

    assert result.notes == "line one\nline two\nother\tค่า"


async def test_AI05_newline_before_a_short_name_that_is_also_math_text_is_kept():
    # PyMuPDF text of the MTH10101 sheets has many lines like these (one symbol per line).
    notes = r"x\ne^{x}\nu = x^{2}\ni) ข้อแรก\nnot clear"
    result, _ = await call_extract_answer(answer_json("x", notes=notes))

    assert result.notes == "x\ne^{x}\nu = x^{2}\ni) ข้อแรก\nnot clear"


async def test_AI05_correctly_escaped_latex_is_not_changed():
    result, _ = await call_extract_answer(answer_json(r"\\frac{1}{x}", r"a\\\\b"))

    assert [line.latex for line in result.lines] == [r"\frac{1}{x}", r"a\\b"]


class MixedText(BaseModel):
    text: MathTextStr
    plain: str


async def call_mixed(text: str, plain: str) -> MixedText:
    """Raw model text for MixedText, with each backslash exactly as the model wrote it."""
    fake = FakeProvider({"extract_answer": [f'{{"text": "{text}", "plain": "{plain}"}}']})
    photo = Image(data=b"\xff\xd8 jpeg bytes", mime_type="image/jpeg")
    return await make_gateway(fake).call(
        "extract_answer", {"image": photo, "problem_text": "x"}, MixedText
    )


async def test_AI05_plain_text_fields_are_not_repaired():
    # Junior's examples from the review of PR #15: a newline before "mid-term" and a tab
    # before a letter are real text, not lost LaTeX backslashes.
    result = await call_mixed("x", r"ตารางคะแนน\nmid-term 30%\tx\ty")

    assert result.plain == "ตารางคะแนน\nmid-term 30%\tx\ty"


async def test_AI05_math_text_is_repaired_only_inside_dollar_signs():
    result = await call_mixed(r"1. จงหา $\frac{1}{x}$ และ $\theta$\nmid-term\tx", "x")

    assert result.text == "1. จงหา $\\frac{1}{x}$ และ $\\theta$\nmid-term\tx"


async def test_AI05_math_text_without_dollar_signs_is_not_changed():
    result = await call_mixed(r"ตารางคะแนน\nmid-term 30%", "x")

    assert result.text == "ตารางคะแนน\nmid-term 30%"


# --- ai-orchestration.md §2.10 retry backoff (review of PR #15) --------------------------------


async def test_ai_orchestration_2_10_retry_waits_backoff_from_config(sleeps: list[float]):
    backoff = get_settings().ai.gateway.retry_backoff_seconds
    fake = FakeProvider({"extract_topics_local": [RuntimeError("503"), VALID_TOPICS]})

    await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert sleeps == [backoff]


async def test_ai_orchestration_2_10_retry_waits_the_delay_the_provider_asked_for(
    sleeps: list[float],
):
    max_wait = get_settings().ai.gateway.max_retry_wait_seconds
    rate_limited = ProviderRateLimited("429", retry_after=max_wait / 2)
    fake = FakeProvider({"extract_topics_local": [rate_limited, VALID_TOPICS]})

    await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert sleeps == [max_wait / 2]


async def test_ai_orchestration_2_10_no_retry_when_provider_asks_to_wait_too_long(
    sleeps: list[float],
):
    max_wait = get_settings().ai.gateway.max_retry_wait_seconds
    rate_limited = ProviderRateLimited("429", retry_after=max_wait + 1)
    fake = FakeProvider({"extract_topics_local": [rate_limited, VALID_TOPICS]})

    with pytest.raises(AIProviderError, match="429"):
        await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    assert sleeps == []
    assert len(fake.requests) == 1


async def test_ai_orchestration_2_10_no_wait_after_the_last_attempt(sleeps: list[float]):
    retries = get_settings().ai.gateway.retries
    fake = FakeProvider({"extract_topics_local": [RuntimeError("503")] * (retries + 1)})

    with pytest.raises(AIProviderError):
        await make_gateway(fake).call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    assert len(sleeps) == retries


# --- AI-01 A3 embed through the gateway (PoC P3b) ----------------------------------------------


class FakeEmbedder:
    """Returns one 2-number vector per text: [length of the text, position in the batch]."""

    def __init__(self, failures: int = 0, delay_s: float = 0.0) -> None:
        self.requests: list[EmbedRequest] = []
        self._failures = failures
        self._delay_s = delay_s

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        self.requests.append(request)
        if self._delay_s:
            await asyncio.sleep(self._delay_s)
        if self._failures:
            self._failures -= 1
            raise RuntimeError("503")
        vectors = [[float(len(text)), float(i)] for i, text in enumerate(request.texts)]
        return EmbedResponse(vectors=vectors, tokens_in=len(request.texts))


async def test_AI01_embed_uses_the_embed_tier_and_keeps_order():
    embedder = FakeEmbedder()

    vectors = await make_gateway(embedder).embed(["a", "bbb"], role="document")

    assert vectors == [[1.0, 0.0], [3.0, 1.0]]
    assert embedder.requests[0].model == get_settings().ai.tiers["embed"].primary
    assert embedder.requests[0].role == "document"


async def test_AI01_embed_sends_batches_of_batch_size_from_config():
    config = get_settings().ai
    embedder = FakeEmbedder()
    gateway = make_gateway(
        embedder,
        embedding=config.embedding.model_copy(update={"batch_size": 2, "dimensions": None}),
    )

    vectors = await gateway.embed(["a", "bb", "ccc", "dddd", "eeeee"], role="query")

    assert [len(r.texts) for r in embedder.requests] == [2, 2, 1]
    assert [v[0] for v in vectors] == [1.0, 2.0, 3.0, 4.0, 5.0]


async def test_AI01_embed_without_texts_makes_no_request():
    embedder = FakeEmbedder()

    assert await make_gateway(embedder).embed([], role="query") == []
    assert embedder.requests == []


async def test_ai_orchestration_2_10_embed_error_is_retried_after_backoff(sleeps: list[float]):
    embedder = FakeEmbedder(failures=1)

    vectors = await make_gateway(embedder).embed(["a"], role="query")

    assert vectors == [[1.0, 0.0]]
    assert sleeps == [get_settings().ai.gateway.retry_backoff_seconds]


async def test_ai_orchestration_2_10_embed_timeout_from_config():
    config = get_settings().ai
    gateway = make_gateway(
        FakeEmbedder(delay_s=0.2),
        embedding=config.embedding.model_copy(update={"timeout_s": 0.01}),
        gateway=config.gateway.model_copy(update={"retries": 0}),
    )

    with pytest.raises(AIProviderError, match="timeout"):
        await gateway.embed(["a"], role="query")


async def test_AI04_embed_call_is_recorded():
    gateway = make_gateway(FakeEmbedder())
    records: list[CallRecord] = []
    gateway.add_listener(records.append)

    await gateway.embed(["a", "b", "c"], role="document")

    assert [(r.purpose, r.status, r.tokens_in) for r in records] == [("embed", "ok", 3)]


# --- vector size (data-model.md: chunks.embedding vector(768), PoC P3b) ------------------------


async def test_AI01_embed_sends_dimensions_from_config():
    config = get_settings().ai
    embedder = FakeEmbedder()
    gateway = make_gateway(
        embedder, embedding=config.embedding.model_copy(update={"dimensions": 2})
    )

    await gateway.embed(["a"], role="document")

    assert embedder.requests[0].dimensions == 2


async def test_AI01_embed_without_dimensions_lets_the_model_choose():
    config = get_settings().ai
    embedder = FakeEmbedder()
    gateway = make_gateway(
        embedder, embedding=config.embedding.model_copy(update={"dimensions": None})
    )

    await gateway.embed(["a"], role="document")

    assert embedder.requests[0].dimensions is None


async def test_AI05_embed_vector_of_another_size_than_config_is_a_provider_error():
    config = get_settings().ai
    gateway = make_gateway(
        FakeEmbedder(),  # returns 2-number vectors
        embedding=config.embedding.model_copy(update={"dimensions": 3}),
        gateway=config.gateway.model_copy(update={"retries": 0}),
    )

    with pytest.raises(AIProviderError, match="dimensions"):
        await gateway.embed(["a"], role="document")


# --- Provider choice from env (specs/features/ai/gemini-vertex.md §2.2) ----------------------


@pytest.fixture
def built_clients(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """genai.Client is replaced by a recorder of the keyword arguments it was built with."""
    built: list[dict] = []

    def recording_client(**kwargs):
        built.append(kwargs)
        return object()

    monkeypatch.setattr(gemini_module.genai, "Client", recording_client)
    return built


def use_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    ai_provider: str = "live",
    gemini_api_key: str = "",
    google_cloud_project: str = "",
    google_cloud_location: str = "global",
) -> None:
    """build_default_gateway() reads these settings instead of the developer's .env."""
    settings = get_settings()
    env = settings.env.model_copy(
        update={
            "ai_provider": ai_provider,
            "ai_model_override": "",
            "gemini_api_key": SecretStr(gemini_api_key),
            "google_cloud_project": google_cloud_project,
            "google_cloud_location": google_cloud_location,
        }
    )
    changed = settings.model_copy(update={"env": env})
    monkeypatch.setattr(settings_module, "get_settings", lambda: changed)


def test_AI02_live_with_only_a_gcp_project_registers_vertex(monkeypatch, built_clients):
    use_env(monkeypatch, google_cloud_project="p-test")

    gateway = gateway_module.build_default_gateway()

    assert sorted(gateway._providers) == ["vertex"]
    assert built_clients[0]["vertexai"] is True
    assert built_clients[0]["project"] == "p-test"
    assert built_clients[0]["location"] == "global"


def test_AI02_live_with_only_an_api_key_registers_gemini(monkeypatch, built_clients):
    use_env(monkeypatch, gemini_api_key="k")

    gateway = gateway_module.build_default_gateway()

    assert sorted(gateway._providers) == ["gemini"]


def test_AI02_live_with_key_and_project_registers_both(monkeypatch, built_clients):
    use_env(monkeypatch, gemini_api_key="k", google_cloud_project="p-test")

    gateway = gateway_module.build_default_gateway()

    assert sorted(gateway._providers) == ["gemini", "vertex"]


def test_AI02_live_without_key_or_project_names_both_variables(monkeypatch, built_clients):
    use_env(monkeypatch)

    with pytest.raises(AIConfigError) as raised:
        gateway_module.build_default_gateway()
    assert "GEMINI_API_KEY" in str(raised.value)
    assert "GOOGLE_CLOUD_PROJECT" in str(raised.value)


def test_AI03_fake_mode_builds_no_google_client(monkeypatch, built_clients):
    use_env(monkeypatch, ai_provider="fake", google_cloud_project="p-test")

    gateway = gateway_module.build_default_gateway()

    assert built_clients == []
    assert isinstance(gateway._single, FakeProvider)


class RecordingProvider:
    def __init__(self) -> None:
        self.requests: list[ProviderRequest] = []

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        return ProviderResponse(text=VALID_TOPICS, tokens_in=10, tokens_out=5)


async def test_AI02_config_model_without_override_goes_to_vertex():
    # extract_topics_local is tier mid, the tier of check_answer (P2).
    config = get_settings().ai
    primary = config.tiers["mid"].primary
    assert primary.startswith("vertex:")
    vertex = RecordingProvider()
    records: list[CallRecord] = []
    gateway = Gateway.live(config=config, prompts_dir=REPO_PROMPTS, providers={"vertex": vertex})
    gateway.add_listener(records.append)

    await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)

    assert vertex.requests[0].model == primary.removeprefix("vertex:")
    assert records[0].provider == "vertex"


async def test_AI02_override_to_a_provider_that_is_not_registered_does_not_fall_back():
    vertex = RecordingProvider()
    gateway = Gateway.live(
        config=get_settings().ai,
        prompts_dir=REPO_PROMPTS,
        providers={"vertex": vertex},
        model_override="gemini:gemini-test",
    )

    with pytest.raises(AIConfigError, match="no provider for model"):
        await gateway.call("extract_topics_local", TOPICS_INPUT, TopicsResult)
    assert vertex.requests == []
