"""The tutor's greeting when the room opens (specs/features/tutor/demo-room.md §2 F).

Code computes the facts (ai-orchestration §2.2.2, directive `open_session` · TM-15); the
model only says them in 2-3 sentences. The room must open whatever happens to the model.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing

from pydantic import BaseModel

from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.models.room import ProgressCardEvent, TokenEvent
from app.services.room_state import PendingProblem
from app.services.tutor_turn import call_scope

log = logging.getLogger(__name__)

# How the progress card levels read to the model (ai-orchestration §2.2.2 table).
LEVEL_NAMES = {
    "not_started": "ยังไม่เริ่ม",
    "weak": "อ่อน",
    "developing": "กำลังดี",
    "passed": "ผ่าน",
}


def opening_facts(card: ProgressCardEvent, pending: PendingProblem | None) -> dict[str, str]:
    """The facts of the greeting; the problem goes without its reference (AM-13)."""
    topics = "\n".join(f"{t.name} · {t.stars} ดาว · {LEVEL_NAMES[t.level]}" for t in card.topics)
    return {
        "days_left": str(card.days_left),
        "readiness": f"{round(card.readiness * 100)}%",
        "topics": topics,
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
