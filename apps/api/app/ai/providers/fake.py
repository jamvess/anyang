"""Fake provider (AI-03): returns scripted text per purpose, never touches the network."""

import asyncio

from app.ai.providers.base import ProviderRequest, ProviderResponse


class FakeProvider:
    """``script`` maps a purpose to the responses returned in order. An ``Exception`` in the
    list is raised instead, to simulate a provider failure."""

    def __init__(self, script: dict[str, list[str | Exception]], delay_s: float = 0.0) -> None:
        self._script = {purpose: list(items) for purpose, items in script.items()}
        self._delay_s = delay_s
        self.requests: list[ProviderRequest] = []
        self.responses_sent: list[ProviderResponse] = []

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        self.requests.append(request)
        if self._delay_s:
            await asyncio.sleep(self._delay_s)
        queue = self._script.get(request.purpose)
        if not queue:
            raise RuntimeError(f"fake provider: no scripted response for {request.purpose!r}")
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        # Rough token estimate (~4 characters per token) so cost logging has numbers in tests.
        response = ProviderResponse(
            text=item, tokens_in=len(request.prompt) // 4 + 1, tokens_out=len(item) // 4 + 1
        )
        self.responses_sent.append(response)
        return response
