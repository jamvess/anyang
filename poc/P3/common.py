"""Shared helpers for PoC P3: paths, the live gateway, call logging and rate-limit backoff.

Run every script from apps/api so its virtualenv and settings are used:
    cd apps/api && uv run python ../../poc/P3/<script>.py
"""

import asyncio
import contextvars
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "apps" / "api"))

from pydantic import BaseModel  # noqa: E402

from app.ai.gateway import AIProviderError, CallRecord, Gateway  # noqa: E402
from app.ai.providers.base import ProviderRequest, ProviderResponse  # noqa: E402
from app.ai.providers.gemini import GeminiProvider  # noqa: E402
from app.settings import AIConfig, get_settings  # noqa: E402

SUBJECT = "mth10101"
RAW = REPO / "evals" / "topics" / SUBJECT / "raw"
LABELS = REPO / "evals" / "topics" / SUBJECT / "labels.json"
OUT = Path(__file__).parent / "out"  # gitignored: contains text of the course files
RESULTS = Path(__file__).parent / "results"  # committed: metrics and topic lists only

# The PoC runs on the Gemini free tier (Jam's choice during development): 5 requests per
# minute per model. Gateway calls run one at a time and start MIN_SECONDS_BETWEEN_REQUESTS
# apart. The wait happens before ai.call, so it is outside the gateway's timeout and outside
# CallRecord.latency_ms (AI time only). A 429 from a gateway-internal retry waits BACKOFF_SECONDS.
FREE_TIER_REQUESTS_PER_MINUTE = 5
MIN_SECONDS_BETWEEN_REQUESTS = 60 / FREE_TIER_REQUESTS_PER_MINUTE + 1
BACKOFF_SECONDS = (30, 60, 90)
# Vertex AI (re-run of 31 Oct · PoC P2 ran 50 calls 1 s apart without a 429): no daily quota,
# so calls only need a short gap. Its results go to out/vertex/ and results/vertex-a5<v>/.
VERTEX_SECONDS_BETWEEN_REQUESTS = 1
VERTEX = "vertex"

_tag: contextvars.ContextVar[str] = contextvars.ContextVar("tag", default="")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class SaveRaw:
    """Wraps a provider and writes every model answer to out/raw/<tag>-<n>.txt, so an answer
    that fails the schema can be read afterwards (the gateway only records the status)."""

    def __init__(self, provider: GeminiProvider, out: Path) -> None:
        self._provider = provider
        self._out = out
        self._count: dict[str, int] = {}

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        response = await self._provider.generate(request)
        tag = _tag.get().replace(":", "_") or request.purpose
        self._count[tag] = self._count.get(tag, 0) + 1
        path = self._out / "raw" / f"{tag}-{self._count[tag]}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response.text, encoding="utf-8")
        return response


def vertex_config(config: AIConfig, small_model: str) -> AIConfig:
    """config/ai.yaml as it is (each purpose on its tier's model, gateway retries as set),
    except tier ``small``, which is still a TODO: it gets ``small_model`` for this run."""
    if not small_model.startswith(f"{VERTEX}:"):
        raise ValueError(f"--small-model must be a vertex: model id, got {small_model!r}")
    tiers = config.tiers | {
        "small": config.tiers["small"].model_copy(update={"primary": small_model})
    }
    return config.model_copy(update={"tiers": tiers})


def label_of(provider: str, model: str) -> str:
    """Folder label of a run: the model id on the free tier, ``vertex`` on Vertex (where each
    tier has its own model, written per call in run.json)."""
    return VERTEX if provider == VERTEX else model.partition(":")[2]


def add_provider_args(parser: Any) -> None:
    parser.add_argument(
        "--provider",
        choices=["gemini", VERTEX],
        default="gemini",
        help="gemini: free tier, one model (AI_MODEL_OVERRIDE); vertex: config/ai.yaml tiers",
    )
    parser.add_argument(
        "--small-model",
        default="",
        help="vertex only: model of tier small (still TODO in config/ai.yaml), e.g. "
        "vertex:gemini-3.5-flash-lite",
    )


class Run:
    """A live gateway whose call records are appended to <out>/calls.jsonl with a tag.
    Also used by poc/P1 (its own ``out`` folder and ``model``)."""

    def __init__(
        self,
        prompt_versions: dict[str, str] | None = None,
        out: Path = OUT,
        model: str | None = None,
        provider: str = "gemini",
        small_model: str = "",
    ) -> None:
        """``prompt_versions`` overrides the prompt of a purpose for this run only, e.g.
        {"extract_topics_local": "v2"}, so a new version is compared before config changes.
        ``provider="vertex"`` runs on Vertex AI with the models of config/ai.yaml and writes to
        ``out/vertex/`` (``small_model`` is required: tier small has no model yet)."""
        settings = get_settings()
        env = settings.env
        purposes = {
            name: p.model_copy(update={"prompt": (prompt_versions or {}).get(name, p.prompt)})
            for name, p in settings.ai.purposes.items()
        }
        self.prompts = {name: p.prompt for name, p in purposes.items()}
        if provider == VERTEX:
            self.model = f"{VERTEX} (config/ai.yaml tiers, small = {small_model})"
            self.out = out / VERTEX
            self.label = VERTEX
            self._gap = VERTEX_SECONDS_BETWEEN_REQUESTS
            config = vertex_config(settings.ai, small_model).model_copy(
                update={"purposes": purposes}
            )
            vertex = GeminiProvider.vertex(env.google_cloud_project, env.google_cloud_location)
            self.gateway = Gateway.live(
                config, env.prompts_dir, {VERTEX: SaveRaw(vertex, self.out)}
            )
        else:
            self.model = model or env.ai_model_override
            self.out = out
            self.label = label_of(provider, self.model)
            self._gap = MIN_SECONDS_BETWEEN_REQUESTS
            # Free tier: a 503 counts against the 20-per-day quota, so the gateway's immediate
            # retry is turned off here and Run.call waits BACKOFF_SECONDS instead. PoC only;
            # config/ai.yaml keeps retries: 1.
            config = settings.ai.model_copy(
                update={
                    "gateway": settings.ai.gateway.model_copy(update={"retries": 0}),
                    "purposes": purposes,
                }
            )
            self.gateway = Gateway.live(
                config,
                env.prompts_dir,
                {"gemini": SaveRaw(GeminiProvider(env.gemini_api_key.get_secret_value()), out)},
                self.model,
            )
        self.records: list[tuple[str, CallRecord]] = []
        self.gateway.add_listener(self._log)
        self._one_at_a_time = asyncio.Lock()
        self._last_start = 0.0

    def _log(self, record: CallRecord) -> None:
        self.records.append((_tag.get(), record))
        self.out.mkdir(parents=True, exist_ok=True)
        with (self.out / "calls.jsonl").open("a", encoding="utf-8") as f:
            line = {"tag": _tag.get(), "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **asdict(record)}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    async def call[T: BaseModel](
        self, tag: str, purpose: str, values: dict[str, Any], schema: type[T]
    ) -> T:
        async with self._one_at_a_time:
            for wait in (*BACKOFF_SECONDS, None):
                gap = self._last_start + self._gap - time.monotonic()
                if gap > 0:
                    await asyncio.sleep(gap)
                self._last_start = time.monotonic()
                _tag.set(tag)
                try:
                    return await self.gateway.call(purpose, values, schema)
                except AIProviderError as error:
                    if wait is None or ("429" not in str(error) and "503" not in str(error)):
                        raise
                    print(f"  {tag}: {str(error)[:120]} -> waiting {wait}s", flush=True)
                    await asyncio.sleep(wait)
        raise AssertionError("unreachable")

    def ai_seconds(self, tag_prefix: str) -> float:
        """Model time only (CallRecord.latency_ms), without free-tier waiting."""
        return sum(r.latency_ms for tag, r in self.records if tag.startswith(tag_prefix)) / 1000

    def tokens(self, tag_prefix: str) -> tuple[int, int]:
        rows = [r for tag, r in self.records if tag.startswith(tag_prefix)]
        return sum(r.tokens_in for r in rows), sum(r.tokens_out for r in rows)
