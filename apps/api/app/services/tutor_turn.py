"""One tutor turn for a text message, PoC P4-lite (specs/features/tutor/tutor-reply-stream.md).

The user's text goes to ``tutor_reply`` through the gateway and every chunk becomes a ``token``
event. Not in P4-lite: stage machine, planner, buddy, context layers 2-9 and saving messages
(spec §9, §10 item 1).
"""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing

from pydantic import BaseModel

from app.ai.gateway import AIProviderError, Gateway
from app.models.room import DoneEvent, ErrorEvent, TokenEvent

log = logging.getLogger(__name__)

# api.md "ระบบช้า": the degrade text when the model fails before saying anything.
DEGRADE_TEXT = "ระบบช้า ลองส่งอีกทีนะ"
# Proposed in spec §10 item 3, pending Junior's list of room error codes (api.md "รอตัดสิน" 3).
AI_UNAVAILABLE = ErrorEvent(code="ai_unavailable", message="The reply stopped before it finished")
# Same code as an unhandled error outside a stream (app/middleware.py); details stay in the log.
INTERNAL_ERROR = ErrorEvent(code="internal_error", message="Internal server error")


async def reply_events(gateway: Gateway, text: str) -> AsyncIterator[tuple[str, BaseModel]]:
    """(event name, payload) pairs of the reply stream, in api.md "SSE events" names.

    Errors become events, because the SSE headers (200) are already sent when the first one
    can happen. The client never sees exception text (spec §2 Endpoint 4-5, AC-19)."""
    sent = False
    try:
        async with aclosing(gateway.stream("tutor_reply", {"message": text})) as chunks:
            async for chunk in chunks:
                sent = True
                yield "token", TokenEvent(speaker="tutor", text=chunk)
    except AIProviderError:
        log.warning("tutor_reply failed after %s", "a partial reply" if sent else "no reply")
        if sent:
            # Part of the reply is on screen already; the web shows its own error text.
            yield "error", AI_UNAVAILABLE
            return
        yield "token", TokenEvent(speaker="tutor", text=DEGRADE_TEXT)
    except Exception:  # config or prompt bug: nothing the student can retry around
        log.exception("tutor_reply stream failed")
        yield "error", INTERNAL_ERROR
        return
    yield "done", DoneEvent()
