"""One tutor turn for a text message, PoC P4-lite (specs/features/tutor/tutor-reply-stream.md).

The user's text goes to ``tutor_reply`` through the gateway and every chunk becomes a ``token``
event. Not in P4-lite: stage machine, planner, buddy, context layers 2-9 and saving messages
(spec §9, §10 item 1).
"""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractContextManager, aclosing, nullcontext

from pydantic import BaseModel

from app.ai.call_context import AICallContext, ai_call_context
from app.ai.gateway import AIProviderError, Gateway
from app.models.room import DoneEvent, ErrorEvent, TokenEvent

log = logging.getLogger(__name__)

# api.md "ระบบช้า": the degrade text when the model fails before saying anything.
DEGRADE_TEXT = "ระบบช้า ลองส่งอีกทีนะ"
# Proposed in spec §10 item 3, pending Junior's list of room error codes (api.md "รอตัดสิน" 3).
AI_UNAVAILABLE = ErrorEvent(code="ai_unavailable", message="The reply stopped before it finished")
# Same code as an unhandled error outside a stream (app/middleware.py); details stay in the log.
INTERNAL_ERROR = ErrorEvent(code="internal_error", message="Internal server error")


def call_scope(call_context: AICallContext | None) -> AbstractContextManager[object]:
    """``ai_call_context`` for the calls made inside it, or nothing without a context."""
    if call_context is None:
        return nullcontext()
    return ai_call_context(
        tenant_id=call_context.tenant_id,
        user_id=call_context.user_id,
        session_id=call_context.session_id,
    )


# tutor_reply/v2 input when no problem is pending (demo-room.md §2 C item 1).
NO_PROBLEM = "none"

Event = tuple[str, BaseModel]


# What runs after the tutor finished without failing: it gets the full text and may add events
# before `done` (demo-room.md §2 B, E: remember the reply, then the next problem).
Tail = Callable[[str], AsyncIterator[Event]]


def reply_events(
    gateway: Gateway,
    text: str,
    call_context: AICallContext | None = None,
    problem: str = NO_PROBLEM,
    conversation: str | None = None,
    tail: Tail | None = None,
) -> AsyncIterator[Event]:
    """The tutor's reply to a text message (``tutor_reply``), as ``tutor_events``. ``problem``
    is the pending problem without its reference (AM-13 · demo-room.md §2 C); ``conversation``
    the recent turns, already escaped (§2 E); left out, the prompt's default applies."""
    values = {"message": text, "problem": problem}
    if conversation is not None:
        values["conversation"] = conversation
    return tutor_events(gateway, "tutor_reply", values, call_context, tail)


async def tutor_events(
    gateway: Gateway,
    purpose: str,
    input: dict[str, str],
    call_context: AICallContext | None = None,
    tail: Tail | None = None,
) -> AsyncIterator[Event]:
    """(event name, payload) pairs of a streamed tutor purpose, in api.md "SSE events" names:
    ``tutor_reply`` here, ``explain_check`` after a verdict (photo-check-in-room.md §2.2).

    Errors become events, because the SSE headers (200) are already sent when the first one
    can happen. The client never sees exception text (spec §2 Endpoint 4-5, AC-19).

    With ``call_context`` the call is logged to ``ai_calls`` under that tenant. It is set here,
    inside the generator that reads the stream, and around ``aclosing``: the gateway reports the
    call when the stream ends, which for a client that leaves early is when ``aclosing`` closes
    it (api-auth.md §2.5).

    ``tail`` gets the full text and adds events before ``done`` only when the tutor finished
    without failing, so a degrade text is never taken for the tutor speaking."""
    said: list[str] = []
    try:
        with call_scope(call_context):
            async with aclosing(gateway.stream(purpose, input)) as chunks:
                async for chunk in chunks:
                    said.append(chunk)
                    yield "token", TokenEvent(speaker="tutor", text=chunk)
    except AIProviderError:
        log.warning("%s failed after %s", purpose, "a partial reply" if said else "no reply")
        if said:
            # Part of the reply is on screen already; the web shows its own error text.
            yield "error", AI_UNAVAILABLE
            return
        yield "token", TokenEvent(speaker="tutor", text=DEGRADE_TEXT)
    except Exception:  # config or prompt bug: nothing the student can retry around
        log.exception("%s stream failed", purpose)
        yield "error", INTERNAL_ERROR
        return
    else:
        if tail is not None:
            async with aclosing(tail("".join(said))) as extra:
                async for event in extra:
                    yield event
    yield "done", DoneEvent()
