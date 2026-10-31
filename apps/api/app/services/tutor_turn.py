"""One tutor turn for a text message, PoC P4-lite (specs/features/tutor/tutor-reply-stream.md).

The user's text goes to ``tutor_reply`` through the gateway and every chunk becomes a ``token``
event. Not in P4-lite: stage machine, planner, buddy, context layers 2-9 and saving messages
(spec §9, §10 item 1).
"""

from collections.abc import AsyncIterator

from pydantic import BaseModel

from app.ai.gateway import AIProviderError, Gateway
from app.models.room import DoneEvent, ErrorEvent, TokenEvent

# api.md "ระบบช้า": the degrade text when the model fails before saying anything.
DEGRADE_TEXT = "ระบบช้า ลองส่งอีกทีนะ"
# Proposed in spec §10 item 3, pending Junior's list of room error codes (api.md "รอตัดสิน" 3).
AI_UNAVAILABLE = "ai_unavailable"


async def reply_events(gateway: Gateway, text: str) -> AsyncIterator[tuple[str, BaseModel]]:
    """(event name, payload) pairs of the reply stream, in api.md "SSE events" names."""
    sent = False
    try:
        async for chunk in gateway.stream("tutor_reply", {"message": text}):
            sent = True
            yield "token", TokenEvent(speaker="tutor", text=chunk)
    except AIProviderError as error:
        if sent:
            # Part of the reply is on screen already; the web shows its own error text.
            yield "error", ErrorEvent(code=AI_UNAVAILABLE, message=str(error))
            return
        yield "token", TokenEvent(speaker="tutor", text=DEGRADE_TEXT)
    yield "done", DoneEvent()
