"""A typed message in the room (tutor-reply-stream.md · demo-room.md §2 C, E, G).

With a pending problem on a local machine, `typed_answer` first decides whether the message is
the answer; if it is, it is checked like a photo (photo_check.typed_answer_events). Otherwise
the tutor replies, knowing the problem and the recent conversation. Everything happens inside
the SSE stream, so a failure ends in a reply, never in an HTTP error.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing

from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.models.check import TypedAnswer
from app.services.photo_check import typed_answer_events
from app.services.room_state import STUDENT, TUTOR, RoomState, conversation_text
from app.services.tutor_turn import NO_PROBLEM, Event, call_scope, reply_events

log = logging.getLogger(__name__)


async def text_message_events(
    gateway: Gateway,
    state: RoomState,
    key: str,
    text: str,
    local: bool,
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    pending = await state.pending_problem(key)
    # The pending problem without its reference (AM-13 · demo-room.md §2 C).
    problem = pending.problem.text if pending else NO_PROBLEM
    # Earlier turns only: the message being answered goes in `message` (§2 E item 4).
    conversation = conversation_text(await state.conversation(key))
    await state.remember(key, STUDENT, text)

    if local and pending:
        lines = await _typed_answer_lines(gateway, problem, conversation, text, call_context)
        if lines:
            # A photo preview still waiting for this problem would check it a second time.
            await state.take_preview(key)
            async with aclosing(
                typed_answer_events(gateway, state, key, pending, lines, call_context)
            ) as events:
                async for event in events:
                    yield event
            return

    async def remember_reply(reply: str) -> AsyncIterator[Event]:
        # Only a finished reply is the tutor speaking (tutor_events calls this then).
        await state.remember(key, TUTOR, reply)
        return
        yield  # an async generator that adds no events

    async with aclosing(
        reply_events(gateway, text, call_context, problem, conversation, remember_reply)
    ) as events:
        async for event in events:
            yield event


async def _typed_answer_lines(
    gateway: Gateway,
    problem: str,
    conversation: str,
    text: str,
    call_context: AICallContext | None,
) -> list[str]:
    """The answer's LaTeX lines, blank ones left out (as for a photo), or [] when the message
    is not an answer or `typed_answer` fails in any way: the tutor replies instead (§2 G)."""
    values = {"problem": problem, "conversation": conversation, "message": text}
    try:
        with call_scope(call_context):
            result = await gateway.call("typed_answer", values, TypedAnswer)
    except Exception:
        log.warning("typed_answer failed; the tutor replies instead", exc_info=True)
        return []
    if not result.is_answer:
        return []
    return [line.strip() for line in result.lines if line.strip()]
