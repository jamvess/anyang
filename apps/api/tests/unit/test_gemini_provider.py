"""Gemini provider: a 429 becomes ProviderRateLimited with the wait Gemini asked for, so the
gateway can back off (ai-orchestration.md §2.10, review of PR #15). No network: the SDK client
is replaced by a stub that raises the SDK's own error."""

import pytest
from google.genai import errors

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
