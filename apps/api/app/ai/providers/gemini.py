"""Gemini through the Gemini API (API key from Google AI Studio). The only module that imports
the Google SDK (AI-01). Vertex AI can replace it later by building the client with
``vertexai=True`` and a project instead of an API key."""

from google import genai
from google.genai import types

from app.ai.providers.base import ProviderRequest, ProviderResponse


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
        usage = response.usage_metadata
        tokens_in = (usage.prompt_token_count or 0) if usage else 0
        # Thinking tokens are billed as output tokens.
        tokens_out = (
            (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0) if usage else 0
        )
        return ProviderResponse(
            text=response.text or "", tokens_in=tokens_in, tokens_out=tokens_out
        )
