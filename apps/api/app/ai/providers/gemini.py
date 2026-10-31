"""Gemini through the Gemini API (API key from Google AI Studio) or Vertex AI (project + location,
credentials from ADC). The only module that imports the Google SDK (AI-01). Both clients share
``generate``, ``stream`` and ``embed`` (specs/features/ai/gemini-vertex.md,
specs/features/tutor/tutor-reply-stream.md)."""

from collections.abc import AsyncIterator

from google import genai
from google.genai import errors, types

from app.ai.providers.base import (
    EmbedRequest,
    EmbedResponse,
    ProviderRateLimited,
    ProviderRequest,
    ProviderResponse,
    StreamUsage,
)


def retry_after_seconds(error_json: dict) -> float | None:
    """The wait a Gemini 429 asks for (``RetryInfo.retryDelay`` such as ``"36s"``), or ``None``."""
    error = error_json.get("error") if isinstance(error_json, dict) else None
    for detail in (error or {}).get("details") or []:
        if str(detail.get("@type", "")).endswith("google.rpc.RetryInfo"):
            delay = str(detail.get("retryDelay", ""))
            try:
                return float(delay.removesuffix("s"))
            except ValueError:
                return None
    return None


def embed_contents(model: str, texts: list[str], role: str) -> tuple[list[str], str | None]:
    """What to send for each text, and the ``task_type`` if the model takes one.

    ``gemini-embedding-001`` takes ``task_type``; ``gemini-embedding-2`` takes a text prefix.
    """
    if model.startswith("gemini-embedding-001"):
        return list(texts), "RETRIEVAL_QUERY" if role == "query" else "RETRIEVAL_DOCUMENT"
    if role == "query":
        return [f"task: search result | query: {text}" for text in texts], None
    return [f"title: none | text: {text}" for text in texts], None


def _contents(request: ProviderRequest) -> list:
    contents: list = [
        types.Part.from_bytes(data=image.data, mime_type=image.mime_type)
        for image in request.images
    ]
    contents.append(request.prompt)
    return contents


def _config(request: ProviderRequest, json_output: bool) -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        temperature=request.temperature,
        max_output_tokens=request.max_tokens,
        response_mime_type="application/json" if json_output else None,
        thinking_config=(
            types.ThinkingConfig(thinking_level=request.thinking) if request.thinking else None
        ),
    )


def _usage(usage) -> tuple[int, int]:
    if not usage:
        return 0, 0
    # Thinking tokens are billed as output tokens.
    tokens_out = (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0)
    return usage.prompt_token_count or 0, tokens_out


def _rate_limited(error: errors.APIError) -> ProviderRateLimited | None:
    if error.code != 429:
        return None
    return ProviderRateLimited(str(error), retry_after_seconds(error.details))


class GeminiProvider:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is empty; set it in .env (docs/team/setup.md A5)")
        # vertexai is always passed: otherwise the SDK reads GOOGLE_GENAI_USE_VERTEXAI.
        self._client = genai.Client(api_key=api_key, vertexai=False)

    @classmethod
    def vertex(cls, project: str, location: str) -> "GeminiProvider":
        """Gemini on Vertex AI. Credentials come from ADC (``gcloud auth application-default
        login`` locally, the service account on Cloud Run); no key file."""
        if not project:
            raise ValueError("GOOGLE_CLOUD_PROJECT is empty; set it in .env for Vertex AI")
        if not location:
            raise ValueError("GOOGLE_CLOUD_LOCATION is empty; set it in .env for Vertex AI")
        provider = cls.__new__(cls)
        provider._client = genai.Client(vertexai=True, project=project, location=location)
        return provider

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        try:
            response = await self._client.aio.models.generate_content(
                model=request.model,
                contents=_contents(request),
                config=_config(request, json_output=True),
            )
        except errors.APIError as error:
            if (limited := _rate_limited(error)) is not None:
                raise limited from error
            raise
        tokens_in, tokens_out = _usage(response.usage_metadata)
        return ProviderResponse(
            text=response.text or "", tokens_in=tokens_in, tokens_out=tokens_out
        )

    async def stream(self, request: ProviderRequest, usage: StreamUsage) -> AsyncIterator[str]:
        """Free text as Gemini writes it. ``usage`` gets the counts of the latest chunk that
        has them (each chunk's usage covers the whole answer so far)."""
        try:
            chunks = await self._client.aio.models.generate_content_stream(
                model=request.model,
                contents=_contents(request),
                config=_config(request, json_output=False),
            )
            try:
                async for chunk in chunks:
                    if chunk.usage_metadata:
                        usage.tokens_in, usage.tokens_out = _usage(chunk.usage_metadata)
                    if chunk.text:
                        yield chunk.text
            finally:
                # Closed early (client left, timeout): stop the HTTP stream to the model now,
                # not when the garbage collector gets to it.
                aclose = getattr(chunks, "aclose", None)
                if aclose is not None:
                    await aclose()
        except errors.APIError as error:
            if (limited := _rate_limited(error)) is not None:
                raise limited from error
            raise

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        texts, task_type = embed_contents(request.model, request.texts, request.role)
        contents: list = list(texts)
        if task_type is None:
            # gemini-embedding-2 is multimodal: plain strings in one request are merged into one
            # vector. One Content per text gives one vector per text (Gemini embeddings docs).
            contents = [types.Content(parts=[types.Part.from_text(text=t)]) for t in texts]
        try:
            response = await self._client.aio.models.embed_content(
                model=request.model,
                contents=contents,
                # Below 3,072 dimensions Gemini does not normalize the vectors; cosine
                # similarity does not need it.
                config=types.EmbedContentConfig(
                    task_type=task_type, output_dimensionality=request.dimensions
                ),
            )
        except errors.APIError as error:
            if error.code == 429:
                raise ProviderRateLimited(str(error), retry_after_seconds(error.details)) from error
            raise
        embeddings = response.embeddings or []
        vectors = [list(embedding.values or []) for embedding in embeddings]
        # Vertex AI reports tokens per embedding (AI-04); the Gemini API does not, so it counts
        # as 0. getattr: the stubs of the older embed tests have no ``statistics`` field.
        tokens_in = 0
        for embedding in embeddings:
            statistics = getattr(embedding, "statistics", None)
            tokens_in += int(statistics.token_count or 0) if statistics else 0
        return EmbedResponse(vectors=vectors, tokens_in=tokens_in)
