"""Fake provider (AI-03): returns scripted text per purpose, never touches the network."""

import asyncio
import re
from collections.abc import AsyncIterator, Awaitable, Callable

from app.ai.providers.base import (
    EmbedRequest,
    EmbedResponse,
    ProviderRequest,
    ProviderResponse,
    StreamUsage,
)

# One streamed reply spelled out chunk by chunk: a str is sent, an Exception is raised at that
# point, and a hook is awaited there (tests use it to hold the stream or make it slow).
StreamStep = str | Exception | Callable[[], Awaitable[None]]
# A function of the request answers from what was sent (the fake mode's vision_extract_pages
# counts the images · ingestion.md §2.7 item 4).
AnswerFn = Callable[[ProviderRequest], str]
ScriptItem = str | Exception | list[StreamStep] | AnswerFn

# A plain str item streams one word at a time, spaces kept, so the chunks always join back.
_WORD = re.compile(r"\S+\s*|\s+")


class Truncated(str):
    """A scripted answer the provider cut at max_tokens (gateway-truncation.md §2.1 item 3):
    ``generate`` returns it with ``truncated=True``; ``stream`` sends it word by word, then marks
    the usage as truncated."""


def _tokens(text: str) -> int:
    # Rough token estimate (~4 characters per token) so cost logging has numbers in tests.
    return len(text) // 4 + 1


class FakeProvider:
    """``script`` maps a purpose to the responses returned in order. An ``Exception`` in the
    list is raised instead, to simulate a provider failure. ``defaults`` answers a purpose
    whose script is used up, every time (the app's fake mode on staging and dev).
    ``record=False`` keeps no history of requests and chunks (for a long-lived process)."""

    def __init__(
        self,
        script: dict[str, list[ScriptItem]],
        delay_s: float = 0.0,
        defaults: dict[str, ScriptItem] | None = None,
        record: bool = True,
    ) -> None:
        self._script = {purpose: list(items) for purpose, items in script.items()}
        self._delay_s = delay_s
        self._defaults = defaults or {}
        self._record = record
        self.requests: list[ProviderRequest] = []
        self.responses_sent: list[ProviderResponse] = []
        self.chunks_sent: list[str] = []

    def _next_item(self, purpose: str) -> ScriptItem:
        queue = self._script.get(purpose)
        if queue:
            return queue.pop(0)
        if purpose in self._defaults:
            return self._defaults[purpose]
        raise RuntimeError(f"fake provider: no scripted response for {purpose!r}")

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        if self._record:
            self.requests.append(request)
        if self._delay_s:
            await asyncio.sleep(self._delay_s)
        item = self._next_item(request.purpose)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, list):
            raise TypeError("fake provider: a chunk list is only for stream()")
        if callable(item) and not isinstance(item, str):
            item = item(request)
        response = ProviderResponse(
            text=str(item),
            tokens_in=_tokens(request.prompt),
            tokens_out=_tokens(item),
            truncated=isinstance(item, Truncated),
        )
        if self._record:
            self.responses_sent.append(response)
        return response

    async def stream(self, request: ProviderRequest, usage: StreamUsage) -> AsyncIterator[str]:
        if self._record:
            self.requests.append(request)
        if self._delay_s:
            await asyncio.sleep(self._delay_s)
        item = self._next_item(request.purpose)
        if isinstance(item, Exception):
            raise item
        if callable(item) and not isinstance(item, str):
            item = item(request)
        steps: list[StreamStep] = _WORD.findall(item) if isinstance(item, str) else item
        usage.tokens_in = _tokens(request.prompt)
        sent = ""
        for step in steps:
            if isinstance(step, Exception):
                raise step
            if callable(step):
                await step()
                continue
            if self._record:
                self.chunks_sent.append(step)
            sent += step
            usage.tokens_out = _tokens(sent)
            yield step
        if isinstance(item, Truncated):
            usage.truncated = True

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        """One fixed vector per text, never random: the first axis only, so the vector is not
        all zeros (ingestion.md §2.7 item 4.3). Its length is the one asked for."""
        size = request.dimensions or 1
        vector = [1.0] + [0.0] * (size - 1)
        tokens = sum(_tokens(text) for text in request.texts)
        return EmbedResponse(vectors=[list(vector) for _ in request.texts], tokens_in=tokens)
