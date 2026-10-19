"""AI gateway, lite version for PoC P3: ``await ai.call(purpose, input, schema)``.

Every AI call in the backend goes through here (AI-01). The gateway loads the prompt version
named in config/ai.yaml, fills its ``{{placeholders}}``, routes to the model of the purpose's
tier (AI-02), validates the output with Pydantic and retries with the error (AI-05), retries
provider errors and timeouts, and reports one ``CallRecord`` per call to listeners (AI-04).

Not in the lite version yet (Junior, S3): fallback provider, circuit breaker, guards, and
writing records to the ``ai_calls`` table.
"""

import asyncio
import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ValidationError

from app.ai.providers.base import Image, Provider, ProviderRequest, ProviderResponse
from app.settings import AIConfig

__all__ = [
    "AIConfigError",
    "AIInputError",
    "AIProviderError",
    "AISchemaError",
    "CallRecord",
    "Gateway",
    "Image",
]

log = logging.getLogger(__name__)

InputValue = str | Image

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")
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
    return _Prompt(version=version, inputs=tuple(meta.get("inputs") or ()), body=body.strip())


def _render(prompt: _Prompt, values: dict[str, InputValue]) -> tuple[str, list[Image]]:
    declared, given = set(prompt.inputs), set(values)
    if missing := declared - given:
        raise AIInputError(f"missing inputs: {sorted(missing)}")
    if unknown := given - declared:
        raise AIInputError(f"inputs not declared in the prompt: {sorted(unknown)}")

    images = [v for name in prompt.inputs if isinstance(v := values[name], Image)]
    texts = {name: v for name, v in values.items() if not isinstance(v, Image)}
    if wrong := [name for name, v in texts.items() if not isinstance(v, str)]:
        raise AIInputError(f"inputs must be str or Image: {wrong}")
    if unfilled := set(_PLACEHOLDER.findall(prompt.body)) - set(texts):
        raise AIInputError(f"placeholders without an input: {sorted(unfilled)}")

    # One pass, so placeholder-like text inside a document is never substituted again.
    return _PLACEHOLDER.sub(lambda m: texts[m.group(1)], prompt.body), images


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
    ) -> None:
        """``provider`` answers every model (fake mode and tests). Use ``Gateway.live`` for
        real providers."""
        self._config = config
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
    ) -> "Gateway":
        """Real providers, chosen by the model id prefix (``gemini:gemini-...``)."""
        return cls(config, prompts_dir, model_override=model_override, providers=providers)

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

        started = time.perf_counter()
        tokens_in = tokens_out = 0
        attempt_prompt = text
        status: Literal["ok", "schema_error", "provider_error"] = "provider_error"
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
            status = "schema_error"
            raise AISchemaError(
                f"{purpose}: output did not match {schema.__name__} after "
                f"{self._config.gateway.schema_retries} schema retries"
            )
        finally:
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
        last_error = ""
        for _ in range(self._config.gateway.retries + 1):
            try:
                return await asyncio.wait_for(provider.generate(request), timeout_s)
            except TimeoutError:
                last_error = f"timeout after {timeout_s}s"
            except Exception as error:  # provider SDKs raise many error types
                last_error = f"{type(error).__name__}: {error}"
        raise AIProviderError(f"{request.purpose}: {last_error}")

    def _emit(self, record: CallRecord) -> None:
        for listener in self._listeners:
            try:
                listener(record)
            except Exception:
                log.exception("AI call listener failed; the call itself is unaffected")


def build_default_gateway() -> Gateway:
    """Gateway from settings: fake provider unless AI_PROVIDER=live."""
    from app.ai.providers.fake import FakeProvider
    from app.settings import get_settings

    settings = get_settings()
    env = settings.env
    if env.ai_provider == "fake":
        return Gateway(settings.ai, env.prompts_dir, FakeProvider({}), env.ai_model_override)

    from app.ai.providers.gemini import GeminiProvider

    providers: dict[str, Provider] = {
        "gemini": GeminiProvider(env.gemini_api_key.get_secret_value())
    }
    return Gateway.live(settings.ai, env.prompts_dir, providers, env.ai_model_override)


_default: Gateway | None = None


async def call[T: BaseModel](purpose: str, input: dict[str, Any], schema: type[T]) -> T:
    """``await ai.call(purpose, input, schema)`` with the gateway built from settings."""
    global _default
    if _default is None:
        _default = build_default_gateway()
    return await _default.call(purpose, input, schema)
