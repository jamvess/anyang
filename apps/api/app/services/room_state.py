"""What the room remembers per session between requests (photo-check-in-room.md §2.4).

The pending problem (what a photo answers) and the handwriting preview waiting to be
confirmed. Proposal pending Junior (spec §10 item 5): the default keeps both in the memory of
the process, like the rate limiter (gateway-guards.md §2.1), so it holds for one Cloud Run
instance only and is used only once an ``ImageStore`` exists. The real one reads and writes
``problems`` and ``messages``.

Every key is ``room_key(tenant_id, session_id)``: a session id alone is not enough, because
no table says yet which tenant owns a session (SA-06).
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Protocol

from fastapi import Depends

from app.models.room import ProgressCardEvent
from app.services.checker import CheckProblem
from app.services.dev_uploads import get_local_mode


@dataclass(frozen=True)
class PendingProblem:
    """``text_latex`` and ``difficulty`` are what the problem card shows; ``topic_id`` is the
    topic whose mastery an answer updates (demo-room.md §2 D)."""

    problem_id: str
    problem: CheckProblem
    text_latex: str = ""
    difficulty: int = 1
    topic_id: str | None = None


@dataclass(frozen=True)
class PendingPreview:
    """The lines of the last ocr_preview, and the problem the photo answered (spec §2.2 item 4:
    a confirm is checked against this problem even if another one is pending by then)."""

    pending: PendingProblem
    lines: tuple[str, ...]


# Problem p1 of session_start.sse with its reference kept on the server (spec §3, §10 item 8):
# the problem event never carries the reference. Pending for every session, and still pending
# after it is checked, until the planner gives the next problem (§10 item 4).
STUB_PROBLEM = PendingProblem(
    problem_id="p1",
    problem=CheckProblem(
        text="แยกตัวประกอบ $x^2 - 49$",
        reference_answer="(x-7)(x+7)",
        answer_format="factored",
        solution_steps=[],
    ),
    text_latex="x^2 - 49",
)


def room_key(tenant_id: str, session_id: str) -> str:
    return f"{tenant_id}/{session_id}"


# Speakers of the remembered conversation (demo-room.md §2 E item 2).
STUDENT = "นักเรียน"
TUTOR = "ติวเตอร์"
# tutor_reply input when nothing is remembered (the prompt's default).
NO_CONVERSATION = "none"


def conversation_text(lines: list[tuple[str, str]]) -> str:
    """One `{role}: {text}` line each, oldest first. Every `<` becomes `&lt;`, so a stored
    message can never close the block or forge a turn (prompts/README.md rule 5)."""
    if not lines:
        return NO_CONVERSATION
    return "\n".join(f"{role}: {text.replace('<', '&lt;')}" for role, text in lines)


class RoomState(Protocol):
    async def pending_problem(self, key: str) -> PendingProblem | None: ...

    async def set_preview(self, key: str, preview: PendingPreview) -> None:
        """A new photo replaces the old preview (api.md v1.7)."""
        ...

    async def take_preview(self, key: str) -> PendingPreview | None:
        """Remove and return the preview in one step, so two confirms sent together cannot
        both check it (one confirm per preview, spec §2.2 item 5)."""
        ...

    async def restore_preview(self, key: str, preview: PendingPreview) -> None:
        """Put a taken preview back when its confirm did not get a verdict, unless a newer
        photo has set one meanwhile (the newer one wins)."""
        ...

    # Hooks of the local demo (demo-room.md §2 B, D); the default state does nothing.

    async def start_session(self, key: str) -> None: ...

    async def record_check(self, key: str, pending: PendingProblem, is_correct: bool) -> None:
        """Count the attempt (BKT) when ``pending`` is still the pending problem."""
        ...

    async def progress_card(self, key: str) -> ProgressCardEvent | None:
        """The card from real mastery, or None when this state keeps none."""
        ...

    async def next_problem(self, key: str, answered: PendingProblem) -> PendingProblem | None:
        """After ``answered`` was checked, make the next problem the pending one and return it;
        None keeps the same one. An answer to a problem that is no longer pending (a stale
        photo preview) moves nothing (self-review PR #115)."""
        ...

    async def remember(self, key: str, role: str, text: str) -> None:
        """Keep one line of the conversation (demo-room.md §2 E); written by the server only."""
        ...

    async def conversation(self, key: str) -> list[tuple[str, str]]:
        """The recent turns, oldest first; empty when this state keeps none."""
        ...


class InMemoryRoomState:
    def __init__(self) -> None:
        self._previews: dict[str, PendingPreview] = {}

    async def pending_problem(self, key: str) -> PendingProblem | None:
        return STUB_PROBLEM

    async def set_preview(self, key: str, preview: PendingPreview) -> None:
        self._previews[key] = preview

    async def take_preview(self, key: str) -> PendingPreview | None:
        return self._previews.pop(key, None)  # no await in between: one step on the loop

    async def restore_preview(self, key: str, preview: PendingPreview) -> None:
        self._previews.setdefault(key, preview)

    async def start_session(self, key: str) -> None:
        self._previews.pop(key, None)

    async def record_check(self, key: str, pending: PendingProblem, is_correct: bool) -> None:
        return None

    async def progress_card(self, key: str) -> ProgressCardEvent | None:
        return None

    async def next_problem(self, key: str, answered: PendingProblem) -> PendingProblem | None:
        return None  # p1 stays pending (photo-check-in-room.md §10 item 4)

    async def remember(self, key: str, role: str, text: str) -> None:
        return None

    async def conversation(self, key: str) -> list[tuple[str, str]]:
        return []


@lru_cache
def _memory_state() -> InMemoryRoomState:
    return InMemoryRoomState()


@lru_cache
def _demo_state() -> RoomState:
    from app.services.demo_room import DemoRoomState  # demo_room builds on this module

    return DemoRoomState()


def get_room_state(local: Annotated[bool, Depends(get_local_mode)]) -> RoomState:
    """FastAPI dependency: the demo state on a local machine (demo-room.md), else the default
    one. Tests replace it with a fresh state."""
    return _demo_state() if local else _memory_state()
