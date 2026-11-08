"""What the room remembers per session between requests (photo-check-in-room.md §2.4).

The pending problem (what a photo answers) and the handwriting preview waiting to be
confirmed. Proposal pending Junior (spec §10 item 5): the default keeps both in the memory of
the process, like the rate limiter (gateway-guards.md §2.1), so it holds for one Cloud Run
instance only. The real one reads and writes ``problems`` and ``messages``.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

from app.services.checker import CheckProblem


@dataclass(frozen=True)
class PendingProblem:
    problem_id: str
    problem: CheckProblem


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
)


class RoomState(Protocol):
    async def pending_problem(self, session_id: str) -> PendingProblem | None: ...

    async def preview(self, session_id: str) -> PendingPreview | None: ...

    async def set_preview(self, session_id: str, preview: PendingPreview) -> None: ...

    async def clear_preview(self, session_id: str) -> None: ...


class InMemoryRoomState:
    def __init__(self) -> None:
        self._previews: dict[str, PendingPreview] = {}

    async def pending_problem(self, session_id: str) -> PendingProblem | None:
        return STUB_PROBLEM

    async def preview(self, session_id: str) -> PendingPreview | None:
        return self._previews.get(session_id)

    async def set_preview(self, session_id: str, preview: PendingPreview) -> None:
        self._previews[session_id] = preview  # a new photo replaces the old preview

    async def clear_preview(self, session_id: str) -> None:
        self._previews.pop(session_id, None)


@lru_cache
def get_room_state() -> RoomState:
    """FastAPI dependency; tests replace it with a fresh ``InMemoryRoomState``."""
    return InMemoryRoomState()
