"""Gemini tells the gateway when an answer was cut at max_output_tokens
(specs/features/ai/gateway-truncation.md §2.1 · AC-1, AC-2). No network: the SDK client is
replaced by a stub that returns the SDK's own response types."""

import pytest
from google.genai import types

from app.ai.providers.base import ProviderRequest, StreamUsage
from app.ai.providers.gemini import GeminiProvider

REQUEST = ProviderRequest(
    purpose="classify_material",
    model="gemini-test",
    prompt="x",
    temperature=0.0,
    max_tokens=300,
)


def response(
    text: str | None, finish: types.FinishReason | None, candidates: bool = True
) -> types.GenerateContentResponse:
    usage = types.GenerateContentResponseUsageMetadata(
        prompt_token_count=820, candidates_token_count=5, thoughts_token_count=291
    )
    if not candidates:
        return types.GenerateContentResponse(candidates=[], usage_metadata=usage)
    parts = [types.Part(text=text)] if text is not None else []
    return types.GenerateContentResponse(
        candidates=[types.Candidate(content=types.Content(parts=parts), finish_reason=finish)],
        usage_metadata=usage,
    )


class StubModels:
    def __init__(
        self,
        answer: types.GenerateContentResponse | None = None,
        chunks: list[types.GenerateContentResponse] | None = None,
    ) -> None:
        self._answer = answer
        self._chunks = chunks or []

    async def generate_content(self, **_kwargs):
        return self._answer

    async def generate_content_stream(self, **_kwargs):
        async def gen():
            for chunk in self._chunks:
                yield chunk

        return gen()


def provider_with(models: StubModels) -> GeminiProvider:
    provider = GeminiProvider(api_key="test-key")
    provider._client = type("Client", (), {"aio": type("Aio", (), {"models": models})()})()
    return provider


# --- AC-1 · generate --------------------------------------------------------------------------


async def test_AI01_gemini_answer_cut_at_max_tokens_is_truncated():
    provider = provider_with(StubModels(response('{"kind": "sh', types.FinishReason.MAX_TOKENS)))

    result = await provider.generate(REQUEST)

    assert result.truncated is True
    assert result.text == '{"kind": "sh'
    assert result.tokens_out == 5 + 291  # thinking counts as output (unchanged)


@pytest.mark.parametrize(
    ("finish", "candidates"),
    [
        (types.FinishReason.STOP, True),
        (types.FinishReason.SAFETY, True),
        (None, True),
        (None, False),
    ],
    ids=["stop", "safety", "no-finish-reason", "no-candidate"],
)
async def test_AI01_gemini_other_endings_are_not_truncated(finish, candidates):
    provider = provider_with(StubModels(response('{"kind": "sheet"}', finish, candidates)))

    result = await provider.generate(REQUEST)

    assert result.truncated is False


# --- AC-2 · stream ----------------------------------------------------------------------------


async def test_AI01_gemini_stream_cut_at_max_tokens_marks_the_usage():
    chunks = [
        response("ลองแยก", None),
        response("ตัวประกอบ", types.FinishReason.MAX_TOKENS),
    ]
    provider = provider_with(StubModels(chunks=chunks))
    usage = StreamUsage()

    text = [chunk async for chunk in provider.stream(REQUEST, usage)]

    assert text == ["ลองแยก", "ตัวประกอบ"]
    assert usage.truncated is True


async def test_AI01_gemini_stream_that_stops_normally_is_not_truncated():
    chunks = [response("ลองแยก", None), response("ตัวประกอบ", types.FinishReason.STOP)]
    provider = provider_with(StubModels(chunks=chunks))
    usage = StreamUsage()

    text = [chunk async for chunk in provider.stream(REQUEST, usage)]

    assert text == ["ลองแยก", "ตัวประกอบ"]
    assert usage.truncated is False
