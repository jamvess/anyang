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
from app.ai.providers.gemini import GeminiProvider  # noqa: E402
from app.settings import get_settings  # noqa: E402

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

_tag: contextvars.ContextVar[str] = contextvars.ContextVar("tag", default="")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class Run:
    """A live gateway whose call records are appended to out/calls.jsonl with a tag."""

    def __init__(self) -> None:
        settings = get_settings()
        env = settings.env
        self.model = env.ai_model_override
        self.gateway = Gateway.live(
            settings.ai,
            env.prompts_dir,
            {"gemini": GeminiProvider(env.gemini_api_key.get_secret_value())},
            env.ai_model_override,
        )
        self.records: list[tuple[str, CallRecord]] = []
        self.gateway.add_listener(self._log)
        self._one_at_a_time = asyncio.Lock()
        self._last_start = 0.0

    def _log(self, record: CallRecord) -> None:
        self.records.append((_tag.get(), record))
        OUT.mkdir(parents=True, exist_ok=True)
        with (OUT / "calls.jsonl").open("a", encoding="utf-8") as f:
            line = {"tag": _tag.get(), "at": time.strftime("%Y-%m-%dT%H:%M:%S"), **asdict(record)}
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

    async def call[T: BaseModel](
        self, tag: str, purpose: str, values: dict[str, Any], schema: type[T]
    ) -> T:
        async with self._one_at_a_time:
            for wait in (*BACKOFF_SECONDS, None):
                gap = self._last_start + MIN_SECONDS_BETWEEN_REQUESTS - time.monotonic()
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

    def tokens(self, tag_prefix: str) -> tuple[int, int]:
        rows = [r for tag, r in self.records if tag.startswith(tag_prefix)]
        return sum(r.tokens_in for r in rows), sum(r.tokens_out for r in rows)
