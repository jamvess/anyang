"""Who an AI call is for: tenant, user and tutor session (specs/features/ai/ai-calls-log.md §2.1).

The JWT dependency sets ``tenant_id`` and ``user_id`` for a request, and a service that knows
the session adds ``session_id``. The ``ai_calls`` listener reads it when the gateway reports a
call; without a context (eval, PoC, requests before the JWT check) the call is only logged.

The context is read when the call ends. For ``ai.stream`` that is after the last chunk, while
the SSE response is being sent, so put the ``with`` inside the generator that reads the stream
(for chat: ``app.services.tutor_turn.reply_events``), not around ``return EventSourceResponse``:
that ``with`` is already over when the stream runs.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AICallContext:
    tenant_id: UUID
    user_id: UUID | None = None
    session_id: UUID | None = None


_context: ContextVar[AICallContext | None] = ContextVar("ai_call_context", default=None)


def current_call_context() -> AICallContext | None:
    return _context.get()


@contextmanager
def ai_call_context(
    tenant_id: UUID, user_id: UUID | None = None, session_id: UUID | None = None
) -> Iterator[AICallContext]:
    """AI calls inside the ``with`` belong to this tenant; an inner ``with`` replaces it."""
    context = AICallContext(tenant_id=tenant_id, user_id=user_id, session_id=session_id)
    token = _context.set(context)
    try:
        yield context
    finally:
        _context.reset(token)
