"""The tutor's greeting when the room opens (specs/features/tutor/demo-room.md §2 F).

Code computes the facts (ai-orchestration §2.2.2, directive `open_session` · TM-15); the
model only says them in 2-3 sentences. The room must open whatever happens to the model.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Any

from pydantic import BaseModel

from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.domain.room import LEVEL_NAMES
from app.models.room import EVENT_MODELS, ProgressCardEvent, TokenEvent
from app.services.photo_check import problem_event, problem_line
from app.services.room_state import TUTOR, PendingProblem, RoomState
from app.services.tutor_turn import call_scope

log = logging.getLogger(__name__)


def topic_lines(card: ProgressCardEvent) -> str:
    """The card's topics for open_session, one per line (levels as in ai-orchestration §2.2.2)."""
    return "\n".join(f"{t.name} · {t.stars} ดาว · {LEVEL_NAMES[t.level]}" for t in card.topics)


def opening_facts(card: ProgressCardEvent, pending: PendingProblem | None) -> dict[str, str]:
    """The facts of the greeting; the problem goes without its reference (AM-13)."""
    return {
        "days_left": str(card.days_left),
        "readiness": f"{round(card.readiness * 100)}%",
        "topics": topic_lines(card),
        "problem": pending.problem.text if pending else "none",
    }


async def greeting_events(
    gateway: Gateway,
    facts: dict[str, str],
    fallback: str,
    said: list[str],
    call_context: AICallContext | None = None,
) -> AsyncIterator[tuple[str, BaseModel]]:
    """Tutor tokens of `open_session`; ``said`` collects what was sent. A failure before the
    first token sends ``fallback``; after one, the greeting just stops (spec §2 F item 5)."""
    try:
        with call_scope(call_context):
            async with aclosing(gateway.stream("open_session", facts)) as chunks:
                async for chunk in chunks:
                    said.append(chunk)
                    yield "token", TokenEvent(speaker="tutor", text=chunk)
    except Exception:  # the room opens anyway: the problem card and done still follow
        log.warning("open_session failed after %s", "a partial greeting" if said else "no greeting")
        if not said:
            said.append(fallback)
            yield "token", TokenEvent(speaker="tutor", text=fallback)


async def opening_events(
    gateway: Gateway,
    state: RoomState,
    key: str,
    recorded: list[tuple[str, dict[str, Any]]],
    card: ProgressCardEvent,
    call_context: AICallContext | None = None,
) -> AsyncIterator[tuple[str, BaseModel]]:
    """The opening stream of a local session (demo-room.md §2 D, F, J): the events of
    session_start.sse with the real card, the greeting from facts, and the problem reached.
    The fixture's own card stays for p1, so its purpose (`probe`) does not change."""
    pending = await state.pending_problem(key)
    said: list[str] = []
    for event, data in recorded:
        if event == "progress_card":
            yield event, card
        elif event == "token":
            facts = opening_facts(card, pending)
            async with aclosing(
                greeting_events(gateway, facts, data["text"], said, call_context)
            ) as greeting:
                async for pair in greeting:
                    yield pair
        elif event == "problem" and pending:
            # What the tutor said is remembered as it was sent (§2 E, F); the card is the
            # problem the student reached (§2 J item 3).
            await state.remember(key, TUTOR, "".join(said))
            await state.remember(key, TUTOR, problem_line(pending))
            same_as_fixture = data.get("problem_id") == pending.problem_id
            yield (
                event,
                (
                    EVENT_MODELS[event].model_validate(data)
                    if same_as_fixture
                    else problem_event(pending)
                ),
            )
        else:
            yield event, EVENT_MODELS[event].model_validate(data)
