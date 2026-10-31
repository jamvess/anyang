"""Fake provider (AI-03): returns scripted text per purpose, never touches the network."""

import asyncio
import re
from collections.abc import AsyncIterator, Awaitable, Callable

from app.ai.providers.base import ProviderRequest, ProviderResponse, StreamUsage

# One streamed reply spelled out chunk by chunk: a str is sent, an Exception is raised at that
# point, and a hook is awaited there (tests use it to hold the stream or make it slow).
StreamStep = str | Exception | Callable[[], Awaitable[None]]
ScriptItem = str | Exception | list[StreamStep]

# A plain str item streams one word at a time, spaces kept, so the chunks always join back.
_WORD = re.compile(r"\S+\s*|\s+")


def _tokens(text: str) -> int:
    # Rough token estimate (~4 characters per token) so cost logging has numbers in tests.
    return len(text) // 4 + 1


class FakeProvider:
    """``script`` maps a purpose to the responses returned in order. An ``Exception`` in the
    list is raised instead, to simulate a provider failure. ``defaults`` answers a purpose
    whose script is used up, every time (the app's fake mode on staging and dev)."""

    def __init__(
        self,
        script: dict[str, list[ScriptItem]],
        delay_s: float = 0.0,
        defaults: dict[str, ScriptItem] | None = None,
    ) -> None:
        self._script = {purpose: list(items) for purpose, items in script.items()}
        self._delay_s = delay_s
        self._defaults = defaults or {}
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
        self.requests.append(request)
        if self._delay_s:
            await asyncio.sleep(self._delay_s)
        item = self._next_item(request.purpose)
        if isinstance(item, Exception):
            raise item
        if isinstance(item, list):
            raise TypeError("fake provider: a chunk list is only for stream()")
        response = ProviderResponse(
            text=item, tokens_in=_tokens(request.prompt), tokens_out=_tokens(item)
        )
        self.responses_sent.append(response)
        return response

    async def stream(self, request: ProviderRequest, usage: StreamUsage) -> AsyncIterator[str]:
        self.requests.append(request)
        if self._delay_s:
            await asyncio.sleep(self._delay_s)
        item = self._next_item(request.purpose)
        if isinstance(item, Exception):
            raise item
        steps: list[StreamStep] = _WORD.findall(item) if isinstance(item, str) else item
        usage.tokens_in = _tokens(request.prompt)
        sent = ""
        for step in steps:
            if isinstance(step, Exception):
                raise step
            if callable(step):
                await step()
                continue
            self.chunks_sent.append(step)
            sent += step
            usage.tokens_out = _tokens(sent)
            yield step
