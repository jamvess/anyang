"""The room state of a session on the database (specs/features/tutor/room-answers-db.md §2.2).

The check flows of the local demo (photo_check.py, room_chat.py) talk to the room only through
`RoomState`; this one reads and writes the session's rows with the user's JWT, so the room with
a token uses the same flows: the pending problem from `problems`, the hint ladder from
`attempts` and `problems.working_steps`, the next problem from the generator of #131, and the
conversation in `messages`. One instance per request, bound to one session; the store calls run
in the thread pool because the Supabase client blocks.

A failure to read or write inside the stream is logged and the stream goes on: what the student
sees is already on screen (§2.2 item 6, §2.3 item 4).
"""

import logging
from collections.abc import Callable
from uuid import UUID

from starlette.concurrency import run_in_threadpool

from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.auth import AuthContext
from app.db.errors import DbUnavailableError
from app.db.room import RoomRepository, SessionRecord
from app.db.room_problems import ProblemRecord, ProblemRepository
from app.domain.checker import CheckResult
from app.domain.room import recent_turns, text_latex_of
from app.models.room import ProgressCardEvent
from app.request_context import get_request_id
from app.services import room_problems
from app.services.checker import CheckProblem
from app.services.room_state import (
    STUDENT,
    TUTOR,
    LadderProgress,
    PendingPreview,
    PendingProblem,
)
from app.settings import get_settings

log = logging.getLogger(__name__)

# Lines the server writes for the tutor's memory, not for the screen (§2.2 item 6): saved with
# role `system`, which the room never shows. The first two are the student's side.
STUDENT_NOTES = ("(ยืนยันคำตอบ)", "(ส่งรูปวิธีทำ)")
TUTOR_NOTES = ("(ผลตรวจ)", "(โจทย์)")

# A photo preview waits a few seconds for its confirm: kept in the memory of the process, like
# the demo (§2.2 item 8 · one instance is enough for the demo, a table after it).
_previews: dict[str, PendingPreview] = {}


def _pending_of(record: ProblemRecord, text_latex: str | None = None) -> PendingProblem:
    return PendingProblem(
        problem_id=str(record.id),
        problem=CheckProblem(
            text=record.text,
            reference_answer=record.reference_answer,
            answer_format=record.answer_format,  # type: ignore[arg-type]  # problems check
            solution_steps=list(record.solution_steps),
        ),
        text_latex=text_latex if text_latex is not None else text_latex_of(record.text),
        difficulty=record.difficulty,
        topic_id=str(record.topic_id),
    )


def saved_role(speaker: str, text: str) -> str:
    """`messages.role` of a remembered line (§2.2 item 6). Only the student's own notes can be
    `system` on the student's side, so a typed message that starts with `(ผลตรวจ)` stays a
    `user` line and never reads as the tutor."""
    if speaker == STUDENT:
        return "system" if text.startswith(STUDENT_NOTES) else "user"
    return "system" if text.startswith(TUTOR_NOTES) else "tutor"


def speaker_of(role: str, text: str) -> str | None:
    """Who said a saved line in the conversation (§2.2 item 7); None leaves it out."""
    if role == "user":
        return STUDENT
    if role == "tutor":
        return TUTOR
    if role == "system":
        return STUDENT if text.startswith(STUDENT_NOTES) else TUTOR
    return None  # buddy and card lines are not the tutor's conversation yet


class DbRoomState:
    def __init__(
        self,
        gateway: Gateway,
        repo: RoomRepository,
        problems: ProblemRepository,
        auth: AuthContext,
        session: SessionRecord,
        *,
        local: bool,
        open_problem: ProblemRecord | None = None,
    ) -> None:
        self._gateway = gateway
        self._repo = repo
        self._problems = problems
        self._auth = auth
        self._session = session
        self._local = local
        # The pending problem once read; the router may already have it.
        self._pending: PendingProblem | None = None
        self._loaded = False
        self._records: dict[str, ProblemRecord] = {}
        if open_problem is not None:
            self._set_pending(open_problem)

    @property
    def call_context(self) -> AICallContext:
        return AICallContext(self._auth.tenant_id, self._auth.user_id, self._session.id)

    def _set_pending(self, record: ProblemRecord | None, text_latex: str | None = None) -> None:
        self._loaded = True
        if record is None:
            self._pending = None
            return
        self._records[str(record.id)] = record
        self._pending = _pending_of(record, text_latex)

    async def _db[T](self, what: str, call: Callable[[], T], default: T) -> T:
        try:
            return await run_in_threadpool(call)
        except DbUnavailableError:
            log.warning(
                "room state: %s failed (request_id=%s, session_id=%s)",
                what,
                get_request_id(),
                self._session.id,
            )
            return default

    async def pending_problem(self, key: str) -> PendingProblem | None:
        if not self._loaded:
            record = await self._db(
                "pending problem", lambda: self._problems.session_problem(self._session.id), None
            )
            self._set_pending(record)
        return self._pending

    async def set_preview(self, key: str, preview: PendingPreview) -> None:
        _previews[key] = preview

    async def take_preview(self, key: str) -> PendingPreview | None:
        return _previews.pop(key, None)

    async def restore_preview(self, key: str, preview: PendingPreview) -> None:
        _previews.setdefault(key, preview)

    async def start_session(self, key: str) -> None:
        return None

    async def record_check(
        self, key: str, pending: PendingProblem, is_correct: bool, independent: bool = True
    ) -> None:
        return None  # BKT into topic_progress is step 8 (§2.2 item 4)

    async def record_answer(
        self,
        key: str,
        pending: PendingProblem,
        lines: list[str],
        result: CheckResult,
        independent: bool,
    ) -> None:
        """One `attempts` row (§2.3 item 1)."""
        if pending.problem_id not in self._records:
            await self.pending_problem(key)  # a confirm checks the problem of its photo
        record = self._records.get(pending.problem_id)
        fields = {
            "tenant_id": self._auth.tenant_id,
            "user_id": self._auth.user_id,
            "problem_id": UUID(pending.problem_id),
            "topic_id": record.topic_id if record else UUID(str(pending.topic_id)),
            "skill_id": record.skill_id if record else None,
            "answer_text": "\n".join(lines),
            "verdict": result.verdict,
            "is_correct": result.is_correct,
            "final_answer_correct": result.final_answer_correct,
            "error_type": result.error_type,
            "first_wrong_line": result.first_wrong_line,
            "evidence": result.evidence,
            "method": result.method,
            "decided_by": result.decided_by,
            "confidence": result.confidence,
            "independent": independent,
        }
        await self._db("insert attempt", lambda: self._problems.add_attempt(**fields), None)

    async def ladder(self, key: str, pending: PendingProblem) -> LadderProgress | None:
        if not self._local:  # AM-07 as it is outside the local demo (§2.2 item 2)
            return None
        problem_id = UUID(pending.problem_id)
        wrong = await self._db(
            "wrong attempts", lambda: self._problems.count_wrong_attempts(problem_id), 0
        )
        steps = await self._db("working steps", lambda: self._problems.working_steps(problem_id), 0)
        return LadderProgress(wrong_before=wrong, steps_before=steps)

    async def note_try(
        self, key: str, pending: PendingProblem, *, wrong: bool = False, steps: int = 0
    ) -> None:
        # A wrong answer is counted by its attempts row (§2.2 item 3).
        if steps:
            problem_id = UUID(pending.problem_id)
            await self._db(
                "add working steps",
                lambda: self._problems.add_working_steps(problem_id, steps),
                None,
            )

    async def progress_card(self, key: str) -> ProgressCardEvent | None:
        return None  # the card comes when the room opens (#131)

    async def next_problem(self, key: str, answered: PendingProblem) -> PendingProblem | None:
        """§2.2 item 5: the answered problem ends first, then a new one in this session. An
        answer to a problem that is no longer the pending one (a stale photo preview) ends it
        and moves nothing else."""
        current = await self.pending_problem(key)
        problem_id = UUID(answered.problem_id)
        await self._db("end problem", lambda: self._problems.end_problem(problem_id), None)
        if current is None or current.problem_id != answered.problem_id:
            return None
        found = await room_problems.next_problem(
            self._gateway,
            self._problems,
            self._auth,
            self._session.exam_prep_id,
            self._session.id,
            self.call_context,
        )
        if found is None:
            self._set_pending(None)
            return None
        record, text_latex = found
        self._set_pending(record, text_latex)
        return self._pending

    async def remember(self, key: str, role: str, text: str) -> None:
        saved = saved_role(role, text)
        await self._db(
            "save message",
            lambda: self._repo.add_message(
                tenant_id=self._auth.tenant_id,
                session_id=self._session.id,
                role=saved,
                content=text,
                input_mode="text" if saved == "user" else None,
            ),
            None,
        )

    async def conversation(self, key: str) -> list[tuple[str, str]]:
        messages = await self._db(
            "conversation", lambda: self._repo.list_messages(self._session.id), []
        )
        lines: list[tuple[str, str]] = []
        for message in messages:
            if message.content is None:
                continue
            speaker = speaker_of(message.role, message.content)
            if speaker is not None:
                # recent_turns starts a turn at each "user" line (the student's side).
                lines.append(("user" if speaker == STUDENT else "tutor", message.content))
        turns = get_settings().learning.session.context_recent_turns
        return [
            (STUDENT if role == "user" else TUTOR, text)
            for role, text in recent_turns(lines, turns)
        ]
