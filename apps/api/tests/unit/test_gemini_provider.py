"""Gemini provider: a 429 becomes ProviderRateLimited with the wait Gemini asked for, so the
gateway can back off (ai-orchestration.md §2.10, review of PR #15). No network: the SDK client
is replaced by a stub that raises the SDK's own error."""

import re
from pathlib import Path

import pytest
from google.genai import errors

import app.ai.providers.gemini as gemini_module
from app.ai.providers.base import EmbedRequest, ProviderRateLimited, ProviderRequest
from app.ai.providers.gemini import GeminiProvider, embed_contents, retry_after_seconds


def quota_error(retry_delay: str | None) -> dict:
    """The JSON body of a Gemini 429 (google.rpc.Status with RetryInfo)."""
    details: list[dict] = [{"@type": "type.googleapis.com/google.rpc.QuotaFailure"}]
    if retry_delay is not None:
        details.append(
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay}
        )
    return {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota.",
            "status": "RESOURCE_EXHAUSTED",
            "details": details,
        }
    }


def test_ai_orchestration_2_10_gemini_retry_delay_is_read_in_seconds():
    assert retry_after_seconds(quota_error("36s")) == 36
    assert retry_after_seconds(quota_error("1.5s")) == 1.5


def test_ai_orchestration_2_10_gemini_without_retry_delay_gives_none():
    assert retry_after_seconds(quota_error(None)) is None
    assert retry_after_seconds({}) is None


class RaisingModels:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def generate_content(self, **_kwargs):
        raise self._error


class StubClient:
    def __init__(self, error: Exception) -> None:
        self.aio = type("Aio", (), {"models": RaisingModels(error)})()


def provider_raising(error: Exception) -> GeminiProvider:
    provider = GeminiProvider(api_key="test-key")
    provider._client = StubClient(error)  # no network in unit tests
    return provider


REQUEST = ProviderRequest(
    purpose="extract_answer", model="gemini-test", prompt="x", temperature=0.0, max_tokens=10
)


async def test_ai_orchestration_2_10_gemini_429_becomes_rate_limited():
    provider = provider_raising(errors.ClientError(429, quota_error("36s")))

    with pytest.raises(ProviderRateLimited) as raised:
        await provider.generate(REQUEST)
    assert raised.value.retry_after == 36


async def test_ai_orchestration_2_10_gemini_other_client_errors_are_not_rate_limits():
    provider = provider_raising(errors.ClientError(400, {"error": {"code": 400}}))

    with pytest.raises(errors.ClientError):
        await provider.generate(REQUEST)


# --- A3 embed (PoC P3b) ----------------------------------------------------------------------
# gemini-embedding-001 takes task_type; gemini-embedding-2 takes a prefix in the text instead
# (https://ai.google.dev/gemini-api/docs/embeddings).


@pytest.mark.parametrize(
    ("role", "task_type"), [("query", "RETRIEVAL_QUERY"), ("document", "RETRIEVAL_DOCUMENT")]
)
def test_AI01_gemini_embedding_001_uses_task_type(role: str, task_type: str):
    assert embed_contents("gemini-embedding-001", ["ลิมิต"], role) == (["ลิมิต"], task_type)


def test_AI01_gemini_embedding_2_uses_text_prefixes():
    assert embed_contents("gemini-embedding-2", ["ลิมิต"], "query") == (
        ["task: search result | query: ลิมิต"],
        None,
    )
    assert embed_contents("gemini-embedding-2", ["ลิมิต"], "document") == (
        ["title: none | text: ลิมิต"],
        None,
    )


class RecordingModels:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def embed_content(self, **kwargs):
        self.calls.append(kwargs)
        embeddings = [
            type("E", (), {"values": [float(i), 0.5]})() for i in range(len(kwargs["contents"]))
        ]
        return type("R", (), {"embeddings": embeddings, "metadata": None})()


async def test_AI01_gemini_embed_returns_one_vector_per_text_in_order():
    provider = GeminiProvider(api_key="test-key")
    models = RecordingModels()
    provider._client = type("C", (), {"aio": type("A", (), {"models": models})()})()

    response = await provider.embed(
        EmbedRequest(model="gemini-embedding-001", texts=["a", "b"], role="query")
    )

    assert response.vectors == [[0.0, 0.5], [1.0, 0.5]]
    call = models.calls[0]
    assert call["model"] == "gemini-embedding-001"
    assert call["contents"] == ["a", "b"]
    assert call["config"].task_type == "RETRIEVAL_QUERY"


async def test_AI01_gemini_embedding_2_sends_one_content_per_text():
    # Found in the P3b smoke test: plain strings to gemini-embedding-2 came back as 1 vector
    # for 50 texts, because the multimodal model merges the parts of one request.
    provider = GeminiProvider(api_key="test-key")
    models = RecordingModels()
    provider._client = type("C", (), {"aio": type("A", (), {"models": models})()})()

    response = await provider.embed(
        EmbedRequest(model="gemini-embedding-2", texts=["a", "b"], role="document")
    )

    assert len(response.vectors) == 2
    contents = models.calls[0]["contents"]
    assert [c.parts[0].text for c in contents] == ["title: none | text: a", "title: none | text: b"]


async def test_AI01_gemini_embed_asks_for_the_dimensions_of_the_request():
    provider = GeminiProvider(api_key="test-key")
    models = RecordingModels()
    provider._client = type("C", (), {"aio": type("A", (), {"models": models})()})()

    await provider.embed(
        EmbedRequest(model="gemini-embedding-2", texts=["a"], role="query", dimensions=768)
    )

    assert models.calls[0]["config"].output_dimensionality == 768


async def test_AI01_gemini_embed_without_dimensions_keeps_the_model_default():
    provider = GeminiProvider(api_key="test-key")
    models = RecordingModels()
    provider._client = type("C", (), {"aio": type("A", (), {"models": models})()})()

    await provider.embed(EmbedRequest(model="gemini-embedding-2", texts=["a"], role="query"))

    assert models.calls[0]["config"].output_dimensionality is None


# --- Vertex AI (specs/features/ai/gemini-vertex.md) --------------------------------------------
# The SDK client is replaced by a recorder, so no test needs ADC or the network.


@pytest.fixture
def built_clients(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """genai.Client is replaced by a recorder of the keyword arguments it was built with."""
    built: list[dict] = []

    def recording_client(**kwargs):
        built.append(kwargs)
        return object()

    monkeypatch.setattr(gemini_module.genai, "Client", recording_client)
    return built


def test_AI01_vertex_client_uses_project_and_location_without_api_key(built_clients):
    GeminiProvider.vertex(project="p-test", location="global")

    assert len(built_clients) == 1
    kwargs = built_clients[0]
    assert kwargs["vertexai"] is True
    assert kwargs["project"] == "p-test"
    assert kwargs["location"] == "global"
    assert kwargs.get("api_key") is None


def test_AI01_api_key_client_says_vertexai_false_even_when_env_asks_for_vertex(
    built_clients, monkeypatch: pytest.MonkeyPatch
):
    # The SDK reads GOOGLE_GENAI_USE_VERTEXAI when vertexai is not passed (spec §2.1).
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")

    GeminiProvider(api_key="k")

    assert built_clients[0]["api_key"] == "k"
    assert built_clients[0]["vertexai"] is False


@pytest.mark.parametrize(
    ("project", "location", "missing"),
    [("", "global", "GOOGLE_CLOUD_PROJECT"), ("p-test", "", "GOOGLE_CLOUD_LOCATION")],
)
def test_AI01_vertex_without_project_or_location_names_the_missing_variable(
    built_clients, project: str, location: str, missing: str
):
    with pytest.raises(ValueError, match=missing):
        GeminiProvider.vertex(project=project, location=location)
    assert built_clients == []


def test_AI01_only_the_gemini_provider_imports_the_google_sdk():
    app_dir = Path(gemini_module.__file__).parents[2]
    allowed = Path(gemini_module.__file__).resolve()
    importers = [
        path.relative_to(app_dir).as_posix()
        for path in app_dir.rglob("*.py")
        if path.resolve() != allowed
        and re.search(
            r"^\s*(from google import genai|import google\.genai|from google\.genai)",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    ]

    assert importers == []


def vertex_provider_with(models) -> GeminiProvider:
    provider = GeminiProvider.vertex(project="p-test", location="global")
    provider._client = type("C", (), {"aio": type("A", (), {"models": models})()})()
    return provider


class StatisticsModels:
    """embed_content answers like Vertex: each embedding may carry statistics.token_count."""

    def __init__(self, token_counts: list[int | None]) -> None:
        self._token_counts = token_counts

    async def embed_content(self, **_kwargs):
        embeddings = [
            type(
                "E",
                (),
                {
                    "values": [float(i)],
                    "statistics": None
                    if count is None
                    else type("S", (), {"token_count": count, "truncated": False})(),
                },
            )()
            for i, count in enumerate(self._token_counts)
        ]
        return type("R", (), {"embeddings": embeddings, "metadata": None})()


EMBED_REQUEST = EmbedRequest(model="gemini-embedding-2", texts=["a", "b"], role="document")


async def test_AI04_vertex_embed_tokens_are_the_sum_of_token_counts(built_clients):
    provider = vertex_provider_with(StatisticsModels([12, 30]))

    response = await provider.embed(EMBED_REQUEST)

    assert response.tokens_in == 42
    assert response.vectors == [[0.0], [1.0]]


@pytest.mark.parametrize(("token_counts", "tokens_in"), [([None, None], 0), ([7, None], 7)])
async def test_AI04_embedding_without_statistics_counts_as_zero_tokens(
    built_clients, token_counts: list[int | None], tokens_in: int
):
    provider = vertex_provider_with(StatisticsModels(token_counts))

    response = await provider.embed(EMBED_REQUEST)

    assert response.tokens_in == tokens_in


class UsageModels:
    async def generate_content(self, **_kwargs):
        usage = type(
            "U",
            (),
            {"prompt_token_count": 100, "candidates_token_count": 20, "thoughts_token_count": 50},
        )()
        return type("R", (), {"text": "{}", "usage_metadata": usage})()


async def test_AI04_vertex_generate_counts_thinking_as_output_tokens(built_clients):
    provider = vertex_provider_with(UsageModels())

    response = await provider.generate(REQUEST)

    assert (response.tokens_in, response.tokens_out) == (100, 70)


async def test_AI02_vertex_429_without_retry_info_has_no_retry_after(built_clients):
    vertex_429 = {
        "error": {
            "code": 429,
            "message": "Resource exhausted. Please try again later.",
            "status": "RESOURCE_EXHAUSTED",
        }
    }
    provider = vertex_provider_with(RaisingModels(errors.ClientError(429, vertex_429)))

    with pytest.raises(ProviderRateLimited) as raised:
        await provider.generate(REQUEST)
    assert raised.value.retry_after is None
