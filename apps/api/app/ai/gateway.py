"""AI gateway, lite version for PoC P3: ``await ai.call(purpose, input, schema)``.

Every AI call in the backend goes through here (AI-01). The gateway loads the prompt version
named in config/ai.yaml, fills its ``{{placeholders}}``, routes to the model of the purpose's
tier (AI-02), validates the output with Pydantic and retries with the error (AI-05), retries
provider errors and timeouts after a backoff (§2.10), and reports one ``CallRecord`` per call
to listeners (AI-04). Lost LaTeX backslashes are repaired by the output models' field types
(``app/ai/latex.py``), not here.

``ai.stream(purpose, input)`` (PoC P4-lite, specs/features/tutor/tutor-reply-stream.md) gives
free text chunk by chunk for purposes with ``stream: true``. It retries only before the first
chunk, because chunks already sent to the user cannot be taken back.

``build_default_gateway()`` adds ``app.db.ai_calls.AICallLog``, which logs every record and
writes the ones with a tenant to ``ai_calls`` (specs/features/ai/ai-calls-log.md).

Each provider has a circuit breaker (specs/features/ai/gateway-guards.md §2.2): while it is
open, calls to that provider fail fast with ``AIProviderError`` and no ``CallRecord``.

Not in the lite version yet: fallback provider, answer-leak check.
"""

import asyncio
import logging
import re
import threading
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ValidationError

from app.ai.circuit_breaker import CircuitBreaker
from app.ai.prompt_data import as_attribute, as_data
from app.ai.providers.base import (
    EmbedRequest,
    Image,
    Provider,
    ProviderRateLimited,
    ProviderRequest,
    ProviderResponse,
    StreamProvider,
    StreamUsage,
)
from app.settings import AIConfig

__all__ = [
    "AIConfigError",
    "AIInputError",
    "AIProviderError",
    "AISchemaError",
    "CallRecord",
    "Gateway",
    "Image",
    "get_gateway",
]

log = logging.getLogger(__name__)

InputValue = str | Image | list[Image]

_sleep = asyncio.sleep  # module attribute so tests can replace it

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
# A tag at the start of a line, its attributes, its contents (prompt-data-blocks.md §2). A tag
# named in the middle of a sentence is not a block.
_DATA_BLOCK = re.compile(r"^<(\w+)((?: [^>\n]*)?)>(.*?)</\1>", re.MULTILINE | re.DOTALL)
_CODE_FENCE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL)
_PREVIOUS_ANSWER_CHARS = 2000


class AIConfigError(Exception):
    """config/ai.yaml or a prompt file is wrong for this call."""


class AIInputError(ValueError):
    """The caller's input does not match the prompt's declared inputs."""


class AIProviderError(RuntimeError):
    """The model could not be reached or timed out after all retries."""


class AISchemaError(ValueError):
    """The model kept answering outside the schema after all schema retries."""


@dataclass(frozen=True)
class CallRecord:
    purpose: str
    provider: str
    model: str
    prompt_version: str
    status: Literal["ok", "schema_error", "provider_error"]
    tokens_in: int
    tokens_out: int
    latency_ms: float
    schema_retries: int


@dataclass(frozen=True)
class _Prompt:
    version: str
    inputs: tuple[str, ...]
    body: str
    # Text used for a declared input the caller leaves out (frontmatter `defaults`), so a new
    # input does not break callers of the earlier contract (prompts/README.md "Frontmatter").
    defaults: dict[str, str] = field(default_factory=dict)


def _load_prompt(prompts_dir: Path, purpose: str, version: str) -> _Prompt:
    path = prompts_dir / purpose / f"{version}.md"
    if not path.exists():
        raise AIConfigError(f"prompt file not found: {path}")
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2) if text.startswith("---") else ("", "", "")
    if not frontmatter:
        raise AIConfigError(f"{path} has no frontmatter (prompts/README.md)")
    meta = yaml.safe_load(frontmatter) or {}
    if meta.get("purpose") != purpose:
        raise AIConfigError(f"{path} declares purpose {meta.get('purpose')!r}, not {purpose!r}")
    if f"v{meta.get('version')}" != version:
        raise AIConfigError(f"{path} declares version {meta.get('version')!r}, not {version!r}")
    inputs = tuple(meta.get("inputs") or ())
    defaults = meta.get("defaults") or {}
    if not isinstance(defaults, dict) or not all(isinstance(v, str) for v in defaults.values()):
        raise AIConfigError(f"{path}: defaults must map input names to text")
    if undeclared := set(defaults) - set(inputs):
        raise AIConfigError(f"{path}: defaults for undeclared inputs {sorted(undeclared)}")
    return _Prompt(version=version, inputs=inputs, body=body.strip(), defaults=defaults)


def _fill(body: str, texts: dict[str, str]) -> str:
    """Puts each value in by where its placeholder sits, so a caller never names a tag and a
    renamed tag stays protected (prompt-data-blocks.md §2). One pass, so placeholder-like text
    inside a value is never substituted again."""
    blocks = list(_DATA_BLOCK.finditer(body))

    def value(placeholder: re.Match[str]) -> str:
        text = texts[placeholder.group(1)]
        for block in blocks:
            if block.start(2) <= placeholder.start() < block.end(2):
                return as_attribute(text)
            if block.start(3) <= placeholder.start() < block.end(3):
                return as_data(text, block.group(1))
        # Outside every block: it still may not close one, or text could forge a whole block.
        for tag in {block.group(1) for block in blocks}:
            text = as_data(text, tag)
        return text

    return _PLACEHOLDER.sub(value, body)


def _render(prompt: _Prompt, values: dict[str, InputValue]) -> tuple[str, list[Image]]:
    values = {**prompt.defaults, **values}
    declared, given = set(prompt.inputs), set(values)
    if missing := declared - given:
        raise AIInputError(f"missing inputs: {sorted(missing)}")
    if unknown := given - declared:
        raise AIInputError(f"inputs not declared in the prompt: {sorted(unknown)}")

    images: list[Image] = []
    texts: dict[str, str] = {}
    for name in prompt.inputs:  # declared order, so attachments keep the prompt's order
        value = values[name]
        if isinstance(value, Image):
            images.append(value)
        elif isinstance(value, list):
            if not all(isinstance(item, Image) for item in value):
                raise AIInputError(f"input {name!r} is a list, so it must contain only images")
            images.extend(value)
        elif isinstance(value, str):
            texts[name] = value
        else:
            raise AIInputError(f"input {name!r} must be str, Image or list[Image]")
    if unfilled := set(_PLACEHOLDER.findall(prompt.body)) - set(texts):
        raise AIInputError(f"placeholders without an input: {sorted(unfilled)}")

    return _fill(prompt.body, texts), images


def _parse[T: BaseModel](text: str, schema: type[T]) -> T:
    stripped = text.strip()
    if match := _CODE_FENCE.match(stripped):
        stripped = match.group(1)
    return schema.model_validate_json(stripped)


def _retry_prompt(prompt: str, answer: str, error: ValidationError) -> str:
    return (
        f"{prompt}\n\nYour previous answer did not match the schema:\n{error}\n\n"
        f"Previous answer:\n{answer[:_PREVIOUS_ANSWER_CHARS]}\n\n"
        "Return only the corrected JSON."
    )


class Gateway:
    def __init__(
        self,
        config: AIConfig,
        prompts_dir: Path,
        provider: Provider | None = None,
        model_override: str | None = None,
        providers: dict[str, Provider] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """``provider`` answers every model (fake mode and tests). Use ``Gateway.live`` for
        real providers. ``clock`` times the circuit breakers (tests pass a fake one)."""
        self._config = config
        self._clock = clock
        self._breakers: dict[str, CircuitBreaker] = {}
        self._prompts_dir = prompts_dir
        self._single = provider
        self._providers = providers or {}
        self._model_override = model_override or None
        self._listeners: list[Callable[[CallRecord], None]] = []

    @classmethod
    def live(
        cls,
        config: AIConfig,
        prompts_dir: Path,
        providers: dict[str, Provider],
        model_override: str | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> "Gateway":
        """Real providers, chosen by the model id prefix (``gemini:gemini-...``)."""
        return cls(
            config, prompts_dir, model_override=model_override, providers=providers, clock=clock
        )

    def breaker(self, provider_name: str) -> CircuitBreaker:
        """The circuit breaker of one provider, made on first use."""
        if provider_name not in self._breakers:
            self._breakers[provider_name] = CircuitBreaker(
                self._config.gateway.circuit_breaker, clock=self._clock, name=provider_name
            )
        return self._breakers[provider_name]

    def _acquire(self, provider_name: str, purpose: str) -> tuple[CircuitBreaker, int]:
        """The provider's breaker and the generation to record the result with, or
        ``AIProviderError`` at once while it is open."""
        breaker = self.breaker(provider_name)
        if not breaker.acquire():
            raise AIProviderError(f"{purpose}: circuit open for provider {provider_name!r}")
        return breaker, breaker.generation

    def add_listener(self, listener: Callable[[CallRecord], None]) -> None:
        self._listeners.append(listener)

    async def call[T: BaseModel](
        self, purpose: str, input: dict[str, InputValue], schema: type[T]
    ) -> T:
        settings = self._config.purposes.get(purpose)
        if settings is None:
            raise AIConfigError(f"unknown purpose {purpose!r}; add it to config/ai.yaml")
        prompt = _load_prompt(self._prompts_dir, purpose, settings.prompt)
        text, images = _render(prompt, input)
        provider_name, provider, model = self._route(settings.tier)
        breaker, generation = self._acquire(provider_name, purpose)

        started = time.perf_counter()
        tokens_in = tokens_out = 0
        attempt_prompt = text
        status: Literal["ok", "schema_error", "provider_error"] = "provider_error"
        provider_failed = False
        schema_retries = 0
        try:
            for schema_retries in range(self._config.gateway.schema_retries + 1):  # noqa: B007
                request = ProviderRequest(
                    purpose=purpose,
                    model=model,
                    prompt=attempt_prompt,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    images=images,
                    thinking=settings.thinking,
                )
                response = await self._generate(provider, request, settings.timeout_s)
                tokens_in += response.tokens_in
                tokens_out += response.tokens_out
                try:
                    result = _parse(response.text, schema)
                except ValidationError as error:
                    attempt_prompt = _retry_prompt(text, response.text, error)
                    continue
                status = "ok"
                return result
            status = "schema_error"  # the model answered: not a provider failure
            raise AISchemaError(
                f"{purpose}: output did not match {schema.__name__} after "
                f"{self._config.gateway.schema_retries} schema retries"
            )
        except AIProviderError:
            provider_failed = True
            raise
        finally:
            breaker.record(_outcome(status != "provider_error", provider_failed), generation)
            self._emit(
                CallRecord(
                    purpose=purpose,
                    provider=provider_name,
                    model=model,
                    prompt_version=prompt.version,
                    status=status,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    schema_retries=schema_retries,
                )
            )

    async def stream(self, purpose: str, input: dict[str, InputValue]) -> AsyncIterator[str]:
        """Free-text chunks of ``purpose`` as the model writes them, empty chunks skipped and
        nothing else changed. ``timeout_s`` of the purpose covers the whole stream. Errors
        before the first chunk are retried like ``call``; after it they end the stream with
        ``AIProviderError``. A stream with no text at all counts as a provider error too (for
        example thinking used up ``max_tokens``). One ``CallRecord`` is sent when the stream
        ends, also when the caller stops reading early (then ``provider_error``)."""
        settings = self._config.purposes.get(purpose)
        if settings is None:
            raise AIConfigError(f"unknown purpose {purpose!r}; add it to config/ai.yaml")
        if not settings.stream:
            raise AIConfigError(f"purpose {purpose!r} has no `stream: true` in config/ai.yaml")
        prompt = _load_prompt(self._prompts_dir, purpose, settings.prompt)
        text, images = _render(prompt, input)
        provider_name, provider, model = self._route(settings.tier)
        if not hasattr(provider, "stream"):
            raise AIConfigError(f"provider {provider_name!r} cannot stream")
        streamer: StreamProvider = provider  # type: ignore[assignment]
        request = ProviderRequest(
            purpose=purpose,
            model=model,
            prompt=text,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            images=images,
            thinking=settings.thinking,
        )
        loop = asyncio.get_running_loop()
        usage = StreamUsage()

        async def first_chunk() -> tuple[AsyncIterator[str], float, str | None]:
            nonlocal usage
            usage = StreamUsage()  # a retry starts counting again
            attempt = streamer.stream(request, usage)
            deadline = loop.time() + settings.timeout_s
            try:
                first = await _next_chunk(attempt)
                if first is None:
                    raise AIProviderError(f"{purpose}: the model returned no text")
                return attempt, deadline, first
            except BaseException:
                await _close(attempt)
                raise

        chunks: AsyncIterator[str] | None = None
        started = time.perf_counter()
        status: Literal["ok", "schema_error", "provider_error"] = "provider_error"
        provider_failed = False
        answered = False  # a caller that stops reading after a chunk is not a provider failure
        breaker, generation = self._acquire(provider_name, purpose)
        try:
            chunks, deadline, chunk = await self._with_retries(
                first_chunk, purpose, settings.timeout_s
            )
            answered = True
            while chunk is not None:
                yield chunk
                try:
                    chunk = await asyncio.wait_for(_next_chunk(chunks), deadline - loop.time())
                except TimeoutError as error:
                    raise AIProviderError(
                        f"{purpose}: timeout after {settings.timeout_s}s"
                    ) from error
                except Exception as error:  # provider SDKs raise many error types
                    raise AIProviderError(f"{purpose}: {type(error).__name__}: {error}") from error
            status = "ok"
        except AIProviderError:
            provider_failed = True
            raise
        finally:
            breaker.record(_outcome(answered, provider_failed), generation)
            if chunks is not None:
                await _close(chunks)
            self._emit(
                CallRecord(
                    purpose=purpose,
                    provider=provider_name,
                    model=model,
                    prompt_version=prompt.version,
                    status=status,
                    tokens_in=usage.tokens_in,
                    tokens_out=usage.tokens_out,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    schema_retries=0,
                )
            )

    async def embed(
        self, texts: list[str], role: Literal["query", "document"]
    ) -> list[list[float]]:
        """A3 ``embed``: one vector per text, in order, from the model of tier ``embed``.
        Texts go in batches of ``embedding.batch_size``; each batch is retried like ``call``."""
        if not texts:
            return []
        provider_name, provider, model = self._route("embed")
        if not hasattr(provider, "embed"):
            raise AIConfigError(f"provider {provider_name!r} cannot embed")
        breaker, generation = self._acquire(provider_name, "embed")
        settings = self._config.embedding
        started = time.perf_counter()
        tokens_in = 0
        status: Literal["ok", "schema_error", "provider_error"] = "provider_error"
        provider_failed = False
        vectors: list[list[float]] = []
        try:
            for start in range(0, len(texts), settings.batch_size):
                request = EmbedRequest(
                    model=model,
                    texts=texts[start : start + settings.batch_size],
                    role=role,
                    dimensions=settings.dimensions,
                )
                response = await self._with_retries(
                    lambda request=request: provider.embed(request), "embed", settings.timeout_s
                )
                if len(response.vectors) != len(request.texts):
                    raise AIProviderError(
                        f"embed: {len(response.vectors)} vectors for {len(request.texts)} texts"
                    )
                if settings.dimensions is not None and any(
                    len(v) != settings.dimensions for v in response.vectors
                ):
                    sizes = sorted({len(v) for v in response.vectors})
                    raise AIProviderError(
                        f"embed: vectors of {sizes} dimensions, config asks for "
                        f"{settings.dimensions}"
                    )
                vectors.extend(response.vectors)
                tokens_in += response.tokens_in
            status = "ok"
            return vectors
        except AIProviderError:
            provider_failed = True
            raise
        finally:
            breaker.record(_outcome(status == "ok", provider_failed), generation)
            self._emit(
                CallRecord(
                    purpose="embed",
                    provider=provider_name,
                    model=model,
                    prompt_version="none",
                    status=status,
                    tokens_in=tokens_in,
                    tokens_out=0,
                    latency_ms=(time.perf_counter() - started) * 1000,
                    schema_retries=0,
                )
            )

    def _route(self, tier: str) -> tuple[str, Provider, str]:
        model = self._model_override or self._config.tiers[tier].primary
        if self._single is not None:
            return "fake", self._single, model
        if "TODO" in model:
            raise AIConfigError(
                f"tier {tier!r} still has a TODO model id ({model}); "
                "set AI_MODEL_OVERRIDE or choose a model in config/ai.yaml"
            )
        prefix, _, model_id = model.partition(":")
        provider = self._providers.get(prefix)
        if provider is None:
            raise AIConfigError(
                f"no provider for model {model!r} (known: {sorted(self._providers)})"
            )
        return prefix, provider, model_id

    async def _generate(
        self, provider: Provider, request: ProviderRequest, timeout_s: float
    ) -> ProviderResponse:
        return await self._with_retries(
            lambda: provider.generate(request), request.purpose, timeout_s
        )

    async def _with_retries[R](
        self, attempt_call: Callable[[], Awaitable[R]], purpose: str, timeout_s: float
    ) -> R:
        """Run ``attempt_call`` with the timeout, retrying provider errors after a backoff."""
        gateway = self._config.gateway
        attempts = gateway.retries + 1
        last_error = ""
        for attempt in range(attempts):
            asked_wait: float | None = None
            try:
                return await asyncio.wait_for(attempt_call(), timeout_s)
            except TimeoutError:
                last_error = f"timeout after {timeout_s}s"
            except ProviderRateLimited as error:
                last_error = f"{type(error).__name__}: {error}"
                asked_wait = error.retry_after
            except Exception as error:  # provider SDKs raise many error types
                last_error = f"{type(error).__name__}: {error}"
            if attempt == attempts - 1:
                break
            wait = gateway.retry_backoff_seconds if asked_wait is None else asked_wait
            if wait > gateway.max_retry_wait_seconds:
                break  # waiting that long inside a chat turn is worse than failing now
            await _sleep(wait)
        raise AIProviderError(f"{purpose}: {last_error}")

    def _emit(self, record: CallRecord) -> None:
        for listener in self._listeners:
            try:
                listener(record)
            except Exception:
                log.exception("AI call listener failed; the call itself is unaffected")


def _outcome(answered: bool, provider_failed: bool) -> bool | None:
    """What a finished call tells the breaker: the provider failed, it answered, or neither
    (the caller was cancelled first, which says nothing about the provider)."""
    if provider_failed:
        return False
    return True if answered else None


async def _next_chunk(chunks: AsyncIterator[str]) -> str | None:
    """Next non-empty chunk, or ``None`` at the end of the stream."""
    async for chunk in chunks:
        if chunk:
            return chunk
    return None


async def _close(chunks: AsyncIterator[str]) -> None:
    """Stop a provider stream so it does not keep reading from the model."""
    aclose = getattr(chunks, "aclose", None)
    if aclose is not None:
        await aclose()


def build_default_gateway() -> Gateway:
    """Gateway from settings: fake provider unless AI_PROVIDER=live. Every call is logged,
    and written to ``ai_calls`` when Supabase is configured (ai-calls-log.md §2.4)."""
    from app.db.ai_calls import AICallLog, SupabaseAICallsWriter
    from app.settings import get_settings

    env = get_settings().env
    gateway = _build_gateway()
    service_key = env.supabase_service_role_key.get_secret_value()
    writer = (
        SupabaseAICallsWriter(env.supabase_url, service_key)
        if env.supabase_url and service_key
        else None
    )
    gateway.add_listener(AICallLog(writer))
    return gateway


def _build_gateway() -> Gateway:
    from app.ai.providers.fake import FakeProvider, StreamStep
    from app.settings import get_settings

    settings = get_settings()
    env = settings.env
    if env.ai_provider == "fake":
        # Staging and dev answer every chat message with the tutor text of the room stub
        # (tutor-reply-stream.md §10 item 4: no buddy in P4-lite's tutor_reply).
        from app import stubs

        reply: list[StreamStep] = [
            data["text"]
            for event, data in stubs.events("tutor_reply")
            if event == "token" and data["speaker"] == "tutor"
        ]
        # record=False: this provider lives as long as the process, so it keeps no history.
        fake = FakeProvider({}, defaults={"tutor_reply": reply}, record=False)
        return Gateway(settings.ai, env.prompts_dir, fake, env.ai_model_override)

    from app.ai.providers.gemini import GeminiProvider

    # The model id prefix in config/ai.yaml picks one of these per call (gemini-vertex.md §2.2).
    providers: dict[str, Provider] = {}
    api_key = env.gemini_api_key.get_secret_value()
    if api_key:
        providers["gemini"] = GeminiProvider(api_key)
    if env.google_cloud_project:
        providers["vertex"] = GeminiProvider.vertex(
            env.google_cloud_project, env.google_cloud_location
        )
    if not providers:
        raise AIConfigError("AI_PROVIDER=live needs GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT in .env")
    return Gateway.live(settings.ai, env.prompts_dir, providers, env.ai_model_override)


_default: Gateway | None = None
_default_lock = threading.Lock()  # FastAPI runs sync dependencies in a thread pool


def get_gateway() -> Gateway:
    """The gateway built from settings, made once. Routers take it as a FastAPI dependency,
    so tests can replace it with ``app.dependency_overrides``."""
    global _default
    if _default is None:
        with _default_lock:
            if _default is None:
                _default = build_default_gateway()
    return _default


async def call[T: BaseModel](purpose: str, input: dict[str, Any], schema: type[T]) -> T:
    """``await ai.call(purpose, input, schema)`` with the gateway built from settings."""
    return await get_gateway().call(purpose, input, schema)


def stream(purpose: str, input: dict[str, Any]) -> AsyncIterator[str]:
    """``async for chunk in ai.stream(purpose, input)`` with the gateway built from settings."""
    return get_gateway().stream(purpose, input)
