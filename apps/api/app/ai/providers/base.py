"""Provider interface for the AI gateway. Providers only talk to a model; the gateway owns
prompts, routing, retries, schema validation and logging (ai-orchestration.md §2.10)."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal, Protocol


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


@dataclass(frozen=True)
class EmbedRequest:
    """Texts to embed (A3 ``embed``). ``role`` lets a model embed a search query differently
    from a document chunk. ``dimensions`` asks for shorter vectors; ``None`` keeps the model's."""

    model: str
    texts: list[str]
    role: Literal["query", "document"]
    dimensions: int | None = None


@dataclass(frozen=True)
class EmbedResponse:
    vectors: list[list[float]]
    tokens_in: int


class EmbedProvider(Protocol):
    async def embed(self, request: EmbedRequest) -> EmbedResponse: ...


class ProviderRateLimited(Exception):
    """The provider refused the request for now (HTTP 429). ``retry_after`` is the wait in
    seconds the provider asked for, or ``None`` when it did not say."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class StreamUsage:
    """Token counts of one stream; the provider fills it in while it streams."""

    tokens_in: int = 0
    tokens_out: int = 0


class Provider(Protocol):
    async def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class StreamProvider(Protocol):
    """Free-text output, chunk by chunk as the model writes it (``tutor_reply``)."""

    def stream(self, request: ProviderRequest, usage: StreamUsage) -> AsyncIterator[str]: ...
