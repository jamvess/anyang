"""Gemini through the Gemini API (API key from Google AI Studio). The only module that imports
the Google SDK (AI-01). Vertex AI can replace it later by building the client with
``vertexai=True`` and a project instead of an API key."""

from google import genai
from google.genai import errors, types

from app.ai.providers.base import (
    EmbedRequest,
    EmbedResponse,
    ProviderRateLimited,
    ProviderRequest,
    ProviderResponse,
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


class GeminiProvider:
    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is empty; set it in .env (docs/team/setup.md A5)")
        self._client = genai.Client(api_key=api_key)

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        contents: list = [
            types.Part.from_bytes(data=image.data, mime_type=image.mime_type)
            for image in request.images
        ]
        contents.append(request.prompt)
        try:
            response = await self._client.aio.models.generate_content(
                model=request.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=request.temperature,
                    max_output_tokens=request.max_tokens,
                    response_mime_type="application/json",
                    thinking_config=(
                        types.ThinkingConfig(thinking_level=request.thinking)
                        if request.thinking
                        else None
                    ),
                ),
            )
        except errors.APIError as error:
            if error.code == 429:
                raise ProviderRateLimited(str(error), retry_after_seconds(error.details)) from error
            raise
        usage = response.usage_metadata
        tokens_in = (usage.prompt_token_count or 0) if usage else 0
        # Thinking tokens are billed as output tokens.
        tokens_out = (
            (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0) if usage else 0
        )
        return ProviderResponse(
            text=response.text or "", tokens_in=tokens_in, tokens_out=tokens_out
        )

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
                config=types.EmbedContentConfig(task_type=task_type),
            )
        except errors.APIError as error:
            if error.code == 429:
                raise ProviderRateLimited(str(error), retry_after_seconds(error.details)) from error
            raise
        vectors = [list(embedding.values or []) for embedding in response.embeddings or []]
        # The Gemini API does not report tokens for embeddings; AI-04 gets 0 until Vertex AI
        # (which reports billable characters) replaces it.
        return EmbedResponse(vectors=vectors, tokens_in=0)
