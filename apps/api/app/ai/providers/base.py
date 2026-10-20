"""Provider interface for the AI gateway. Providers only talk to a model; the gateway owns
prompts, routing, retries, schema validation and logging (ai-orchestration.md §2.10)."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Image:
    data: bytes
    mime_type: str


@dataclass(frozen=True)
class ProviderRequest:
    purpose: str
    model: str
    prompt: str
    temperature: float
    max_tokens: int
    images: list[Image] = field(default_factory=list)
    thinking: str | None = None


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    tokens_in: int
    tokens_out: int


class ProviderRateLimited(Exception):
    """The provider refused the request for now (HTTP 429). ``retry_after`` is the wait in
    seconds the provider asked for, or ``None`` when it did not say."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class Provider(Protocol):
    async def generate(self, request: ProviderRequest) -> ProviderResponse: ...
