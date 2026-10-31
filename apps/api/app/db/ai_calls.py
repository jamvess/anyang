"""``ai_calls`` log of the AI gateway (AI-04 · specs/features/ai/ai-calls-log.md).

``AICallLog`` is a gateway listener. Every ``CallRecord`` becomes one JSON line on the
``app.ai.calls`` logger (Cloud Logging on Cloud Run). When the call has a tenant
(``app.ai.call_context``) the same row is also inserted into ``ai_calls``, in the background so
the call never waits for the database (NFR-P1). Inserts run one at a time on the listener's own
thread, so a slow database cannot take the event loop's shared thread pool from other work. A
failed insert is logged and dropped.
"""

import asyncio
import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol

from supabase import Client, ClientOptions, create_client

from app.ai.call_context import AICallContext, current_call_context
from app.ai.gateway import CallRecord
from app.request_context import get_request_id

log = logging.getLogger("app.ai.calls")

# CallRecord.prompt_version of calls without a prompt (embed).
_NO_PROMPT = "none"


class AICallsWriter(Protocol):
    def insert(self, row: dict[str, Any]) -> None: ...


def _status(record: CallRecord) -> str:
    """CallRecord status → the values allowed by the ai_calls check constraint (spec §2.2)."""
    if record.status != "ok":
        return "error"
    return "schema_retry" if record.schema_retries else "ok"


def _text(value: object | None) -> str | None:
    return None if value is None else str(value)


def to_row(
    record: CallRecord, context: AICallContext | None, request_id: str | None
) -> dict[str, Any]:
    """One ``ai_calls`` row (without ``id`` and ``created_at``), JSON-ready."""
    return {
        "tenant_id": _text(context and context.tenant_id),
        "user_id": _text(context and context.user_id),
        "session_id": _text(context and context.session_id),
        "request_id": request_id,
        "purpose": record.purpose,
        "provider": record.provider,
        "model": record.model,
        "prompt_version": None if record.prompt_version == _NO_PROMPT else record.prompt_version,
        "tokens_in": record.tokens_in,
        "tokens_out": record.tokens_out,
        "cached_tokens": None,  # providers do not report cached tokens yet (spec §9)
        "latency_ms": round(record.latency_ms),
        "cost_usd": None,  # no price table yet (spec §10 item 2)
        "status": _status(record),
        "fallback_used": False,  # the lite gateway has no fallback provider
    }


class AICallLog:
    """Gateway listener: log every call, insert the ones that have a tenant."""

    def __init__(self, writer: AICallsWriter | None = None) -> None:
        self.writer = writer
        self._executor = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="ai_calls")
            if writer is not None
            else None
        )
        self._pending: set[asyncio.Future[None]] = set()

    def __call__(self, record: CallRecord) -> None:
        context = current_call_context()
        row = to_row(record, context, get_request_id())
        log.info(json.dumps(row | {"schema_retries": record.schema_retries}, ensure_ascii=False))
        if context is None or self.writer is None:
            return
        # The gateway emits records from async code only, so a running loop is always there.
        future = asyncio.get_running_loop().run_in_executor(
            self._executor, _insert, self.writer, row
        )
        self._pending.add(future)
        future.add_done_callback(self._pending.discard)

    async def flush(self) -> None:
        """Wait for the inserts still running, also ones started while waiting (tests, and app
        shutdown later)."""
        while self._pending:
            await asyncio.gather(*self._pending)


def _insert(writer: AICallsWriter, row: dict[str, Any]) -> None:
    try:
        writer.insert(row)
    except Exception as error:  # DB down, network, constraint: the call is unaffected
        log.warning(
            "ai_calls insert failed (purpose=%s, request_id=%s): %s: %s",
            row["purpose"],
            row["request_id"],
            type(error).__name__,
            error,
        )


class SupabaseAICallsWriter:
    """Inserts with the service role key: users may only select ``ai_calls`` (RLS), so the
    backend writes every row and always sets ``tenant_id`` itself (apps/api/CLAUDE.md)."""

    def __init__(self, url: str, service_role_key: str) -> None:
        self._url = url
        self._key = service_role_key
        self._client: Client | None = None
        self._lock = threading.Lock()  # inserts run off the event loop thread

    def _get_client(self) -> Client:
        # Made on the first insert, so building the gateway opens no connection.
        with self._lock:
            if self._client is None:
                options = ClientOptions(auto_refresh_token=False, persist_session=False)
                self._client = create_client(self._url, self._key, options)
            return self._client

    def insert(self, row: dict[str, Any]) -> None:
        self._get_client().table("ai_calls").insert(row).execute()
