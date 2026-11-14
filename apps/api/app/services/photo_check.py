"""A photo answer in the room: extract_answer → ocr_preview, then confirm → checker → verdict →
explain_check (specs/features/check/photo-check-in-room.md).

P1 (``extract_answer``) reads the handwriting; P2 (``check_answer`` service: SymPy + classifier
+ merge rules) checks the lines the user confirmed; ``explain_check`` turns the result into the
tutor's explanation (AM-07). Code decides, the LLM speaks (CLAUDE.md rule 1). Storage and the
database come later (spec §9): the image is read through ``ImageStore`` and the pending problem
and preview live in ``RoomState`` (app/services/room_state.py), under ``room_key``.
"""

import json
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import aclosing
from pathlib import Path
from typing import Annotated, Protocol

from fastapi import Depends
from pydantic import BaseModel

from app.ai.call_context import AICallContext
from app.ai.gateway import AIProviderError, AISchemaError, Gateway, Image
from app.domain.checker import CheckResult, working_missing, working_steps
from app.domain.hint_ladder import Directive, attempt_outcome, decide_directive, unfinished
from app.models.room import (
    DoneEvent,
    OcrLine,
    OcrPreviewEvent,
    ProblemEvent,
    TokenEvent,
    VerdictEvent,
)
from app.models.scope_ai import ExtractAnswerResult
from app.services.checker import (
    CheckProblem,
    check_answer,
    number_lines,
    solution_steps_text,
)
from app.services.dev_uploads import LocalImageStore, get_local_mode, get_local_upload_dir
from app.services.room_state import (
    STUDENT,
    TUTOR,
    LadderProgress,
    PendingPreview,
    PendingProblem,
    RoomState,
)
from app.services.tutor_turn import DEGRADE_TEXT, INTERNAL_ERROR, call_scope, tutor_events
from app.settings import get_settings

log = logging.getLogger(__name__)
# AM-03: which lines the user corrected on the card (spec §2.2 item 3) · Cloud Logging for now.
confirm_log = logging.getLogger("app.ocr.confirm")

# Tutor lines that come from code, not from a model (spec §2.1).
LOOKING = "ขอดูก่อนนะ"
CHECK_PLEASE = "เช็คให้หน่อยว่าอ่านถูกไหม"
UNREADABLE = "รูปนี้อ่านไม่ออก ลองถ่ายใหม่ให้ชัดขึ้นอีกนิดนะ"
# UC-04 E9 with no intent router yet (spec §10 item 4 · proposal pending Junior).
NO_PENDING_PROBLEM = "ตอนนี้ยังไม่มีโจทย์ที่รอคำตอบ ส่งคำถามเป็นข้อความได้เลยนะ"
# Before the next problem card of the local demo (demo-room.md §2 B item 2).
NEXT_PROBLEM = "ข้อต่อไปนะ"
# The remembered conversation line when a right answer has no working (demo-room.md §2 I).
NO_WORKING_LINE = "(ผลตรวจ) ขาดวิธีทำ"
# The remembered lines of the hint ladder (demo-room.md §2 K item 5).
UNFINISHED_LINE = "(ผลตรวจ) ถูกแล้ว ยังไม่จบ"
GAVE_UP_LINE = "(ผลตรวจ) ขอเฉลย"
# An explain_check input with nothing in it (§2 K items 6-7).
NONE = "none"

HINTS: frozenset[Directive] = frozenset({"hint_1", "hint_2"})
# The problem is still open: no reference for the tutor (AM-13), and the same card again.
OPEN_DIRECTIVES: frozenset[Directive] = HINTS | {"continue"}
SAME_PROBLEM_AGAIN: frozenset[Directive] = OPEN_DIRECTIVES | {"ask_working"}

Event = tuple[str, BaseModel]


class ImageStore(Protocol):
    async def read(self, path: str) -> Image | None:
        """The uploaded file at ``path``, or None when there is none. The router checks the
        size of what comes back; a Storage-backed store should also refuse to download an
        object whose metadata is over ``guards.max_image_mb`` (Junior · self-review PR #114)."""
        ...


def get_image_store(
    local: Annotated[bool, Depends(get_local_mode)],
    upload_dir: Annotated[Path, Depends(get_local_upload_dir)],
) -> ImageStore | None:
    """FastAPI dependency. None means no Storage yet (spec §2.4): photo messages and
    ocr/confirm keep their stubs until Junior wires Supabase Storage and the real /uploads.
    On a local machine the photos come from the local upload folder (demo-room.md §2 A)."""
    return LocalImageStore(upload_dir) if local else None


def _tutor(text: str) -> Event:
    return "token", TokenEvent(speaker="tutor", text=text)


async def photo_events(
    gateway: Gateway,
    state: RoomState,
    key: str,
    pending: PendingProblem,
    image: Image,
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    """SSE of a photo message (spec §2.1 items 4-6). The caption never reaches the model."""
    yield _tutor(LOOKING)  # before the model call, so the user sees the photo was taken
    try:
        with call_scope(call_context):
            result = await gateway.call(
                "extract_answer",
                {"image": image, "problem_text": pending.problem.text},
                ExtractAnswerResult,
            )
    except (AIProviderError, AISchemaError):
        log.warning("extract_answer failed; the earlier preview, if any, stays")
        yield _tutor(DEGRADE_TEXT)
        yield "done", DoneEvent()
        return
    except Exception:
        log.exception("extract_answer failed")
        yield "error", INTERNAL_ERROR
        return

    # A blank line could not be confirmed (the confirm body refuses blank lines), so it is
    # left out; the confirm body is stripped too, so the preview is kept stripped (AM-03).
    lines = [
        OcrLine(latex=line.latex.strip(), confidence=line.confidence)
        for line in result.lines
        if line.latex.strip()
    ]
    if not lines:  # unreadable or not an answer (UC-04 E1); the old preview stays
        yield _tutor(UNREADABLE)
        await state.remember(key, TUTOR, f"{LOOKING} {UNREADABLE}")
        yield "done", DoneEvent()
        return
    # Confirmed every time, whatever the confidence (AM-02 · ocr.always_confirm, P1).
    await state.set_preview(
        key, PendingPreview(pending=pending, lines=tuple(line.latex for line in lines))
    )
    yield "ocr_preview", OcrPreviewEvent(lines=lines)
    yield _tutor(CHECK_PLEASE)
    await state.remember(key, TUTOR, f"{LOOKING} {CHECK_PLEASE}")
    yield "done", DoneEvent()


def _check_result_text(result: CheckResult, no_working: bool = False, evidence: bool = True) -> str:
    fields = {
        "verdict": result.verdict,
        "first_wrong_line": result.first_wrong_line,
        "error_type": result.error_type,
        "evidence": result.evidence if evidence else None,
        "method": result.method,
        # missing: the final answer is right but has no working (demo-room.md §2 I)
        "working": "missing" if no_working else "ok",
    }
    return "\n".join(f"{name}: {'none' if v is None else v}" for name, v in fields.items())


def _log_edits(session_id: str, preview: PendingPreview, lines: Sequence[str]) -> None:
    edited = [
        n for n, (old, new) in enumerate(zip(preview.lines, lines, strict=True), 1) if old != new
    ]
    confirm_log.info(
        json.dumps({"session_id": session_id, "line_count": len(lines), "edited_lines": edited})
    )


async def _check(
    gateway: Gateway, problem: CheckProblem, lines: list[str], call_context: AICallContext | None
) -> tuple[CheckResult, VerdictEvent] | list[Event]:
    """The checker of P2 and the verdict event, or the events that end the stream when it
    fails: the classifier (AI) → "ระบบช้า" (spec §10 item 2) · anything else → internal_error."""
    try:
        with call_scope(call_context):
            result = await check_answer(problem, lines, gateway=gateway)
        verdict = VerdictEvent(
            verdict=result.verdict,
            first_wrong_line=result.first_wrong_line,
            error_type=result.error_type,
        )
    except (AIProviderError, AISchemaError):
        log.warning("check_answer classifier failed; the answer can be sent again")
        return [_tutor(DEGRADE_TEXT), ("done", DoneEvent())]
    except Exception:
        log.exception("check_answer failed")
        return [("error", INTERNAL_ERROR)]
    return result, verdict


async def confirm_events(
    gateway: Gateway,
    state: RoomState,
    key: str,
    session_id: str,
    preview: PendingPreview,
    lines: list[str],
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    """SSE of ocr/confirm (spec §2.2 items 3-8): verdict first, then the tutor explains.

    The router has already taken ``preview`` out of the state (``take_preview``). Until the
    verdict is built it is put back on every way out, so the user can confirm again (§2.2
    item 7); a newer photo that arrived meanwhile wins."""
    checked = False
    try:
        outcome = await _check(gateway, preview.pending.problem, lines, call_context)
        if isinstance(outcome, list):
            for event in outcome:
                yield event
            return
        checked = True  # one confirm per preview (§2.2 item 5)
    finally:
        if not checked:
            await state.restore_preview(key, preview)

    result, verdict = outcome
    _log_edits(session_id, preview, lines)
    await state.remember(key, STUDENT, f"(ยืนยันคำตอบ) {' · '.join(lines)}")
    async with aclosing(
        _verdict_and_explanation(
            gateway, state, key, preview.pending, lines, result, verdict, call_context
        )
    ) as events:
        async for event in events:
            yield event


async def typed_answer_events(
    gateway: Gateway,
    state: RoomState,
    key: str,
    pending: PendingProblem,
    lines: list[str],
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    """A typed answer (demo-room.md §2 G): checked like a confirmed photo, with no card to
    confirm (UC-04 A2) and nothing to log for AM-03. The caller has remembered the message."""
    outcome = await _check(gateway, pending.problem, lines, call_context)
    if isinstance(outcome, list):
        for event in outcome:
            yield event
        return
    result, verdict = outcome
    async with aclosing(
        _verdict_and_explanation(gateway, state, key, pending, lines, result, verdict, call_context)
    ) as events:
        async for event in events:
            yield event


async def _verdict_and_explanation(
    gateway: Gateway,
    state: RoomState,
    key: str,
    pending: PendingProblem,
    lines: list[str],
    result: CheckResult,
    verdict: VerdictEvent,
    call_context: AICallContext | None,
) -> AsyncIterator[Event]:
    """After a check, photo or typed (spec §2.2 items 5-8 · demo-room §2 B, D, E, I, K): code
    picks the directive (app/domain/hint_ladder.py), then the verdict, the tutor's explanation,
    and the same problem again or the next one.

    Before the explanation, so it holds even if the tutor fails: the wrong answer or the right
    steps are counted on the ladder (§2 K item 4), or the problem's one attempt is recorded."""
    settings = get_settings().learning
    progress = await state.ladder(key, pending)
    steps = working_steps(lines)
    no_working = working_missing(
        result.verdict,
        steps + (progress.steps_before if progress else 0),  # §2 K item 3
        settings.checker,
    )
    directive = decide_directive(
        result.verdict,
        give_up=False,
        unfinished=unfinished(result.verdict, lines[-1]) if lines else False,
        no_working=no_working,
        wrong_before=progress.wrong_before if progress else None,
        cfg=settings.tutoring,
    )
    if directive == "continue":
        await state.note_try(key, pending, steps=steps)
        await state.remember(key, TUTOR, UNFINISHED_LINE)
    elif directive == "ask_working":
        await state.remember(key, TUTOR, NO_WORKING_LINE)
    else:
        if directive in HINTS:
            await state.note_try(key, pending, wrong=True)
            independent = True
        else:
            independent = await _record_attempt(
                state, key, pending, directive, progress, result.is_correct
            )
        # Every answer with a verdict (room-answers-db.md §2.3 · PM-01); the demo keeps none.
        await state.record_answer(key, pending, lines, result, independent)
        await state.remember(key, TUTOR, _verdict_line(result))
        yield "verdict", verdict
    explain_input = _explain_input(
        pending.problem,
        directive,
        number_lines(lines),
        # The classifier's evidence often states the right value of the wrong line, so it is
        # left out while the problem is open, like the reference (AM-13 · self-review PR #127).
        _check_result_text(result, no_working, evidence=directive not in OPEN_DIRECTIVES),
    )
    async with aclosing(
        _explanation(gateway, state, key, pending, directive, explain_input, call_context)
    ) as events:
        async for event in events:
            yield event


async def give_up_events(
    gateway: Gateway,
    state: RoomState,
    key: str,
    pending: PendingProblem,
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    """The student gave up on the pending problem (demo-room.md §2 K item 6): nothing to
    check, so no verdict; the full solution, the attempt counted as wrong, the next problem.
    The caller has remembered the message."""
    progress = await state.ladder(key, pending)
    directive = decide_directive(
        None,
        give_up=True,
        unfinished=False,
        no_working=False,
        wrong_before=progress.wrong_before if progress else None,
        cfg=get_settings().learning.tutoring,
    )
    await _record_attempt(state, key, pending, directive, progress, False)
    await state.remember(key, TUTOR, GAVE_UP_LINE)
    explain_input = _explain_input(pending.problem, directive, NONE, NONE)
    async with aclosing(
        _explanation(gateway, state, key, pending, directive, explain_input, call_context)
    ) as events:
        async for event in events:
            yield event


async def _record_attempt(
    state: RoomState,
    key: str,
    pending: PendingProblem,
    directive: Directive,
    progress: LadderProgress | None,
    is_correct: bool,
) -> bool:
    """The problem's one attempt (demo: BKT · §2 D, §2 K item 8). With no ladder, every
    finished answer counts as it is, independent. Returns whether it was independent."""
    if progress is None:
        await state.record_check(key, pending, is_correct)
        return True
    outcome = attempt_outcome(directive, progress.wrong_before, get_settings().learning.tutoring)
    if outcome is None:
        return True
    await state.record_check(key, pending, *outcome)
    return outcome[1]


def _explain_input(
    problem: CheckProblem, directive: Directive, answer_lines: str, check_result: str
) -> dict[str, str]:
    # The tutor shows the right value and method only once the problem is over (§2.2.4). While
    # it is still open (continue, hints) code leaves the reference out (AM-13 · §2 K item 7).
    still_open = directive in OPEN_DIRECTIVES
    return {
        "problem": problem.text,
        "reference_answer": NONE if still_open else problem.reference_answer,
        "solution_steps": NONE if still_open else solution_steps_text(problem),
        "answer_lines": answer_lines,
        "check_result": check_result,
        "directive": directive,
    }


async def _explanation(
    gateway: Gateway,
    state: RoomState,
    key: str,
    pending: PendingProblem,
    directive: Directive,
    explain_input: dict[str, str],
    call_context: AICallContext | None,
) -> AsyncIterator[Event]:
    async def after_explaining(explanation: str) -> AsyncIterator[Event]:
        # Runs only when the explanation finished (tutor_events), so a degrade text is never
        # remembered as the tutor speaking (§2 E item 2).
        await state.remember(key, TUTOR, explanation)
        if directive in SAME_PROBLEM_AGAIN:
            # The same problem again at the bottom; the canvas keeps the drawing (§2 I item 6,
            # §2 K item 4).
            await state.remember(key, TUTOR, problem_line(pending))
            yield "problem", problem_event(pending)
            return
        # Demo only (demo-room.md §2 B): the default state has no next problem. No progress
        # card here: it comes when the room opens (§2 J item 1).
        if upcoming := await state.next_problem(key, pending):
            # Remembered before it is sent: a client that leaves now still finds it (§2 E).
            await state.remember(key, TUTOR, NEXT_PROBLEM)
            await state.remember(key, TUTOR, problem_line(upcoming))
            yield _tutor(NEXT_PROBLEM)
            yield "problem", problem_event(upcoming)

    async with aclosing(
        tutor_events(gateway, "explain_check", explain_input, call_context, after_explaining)
    ) as events:
        async for event in events:
            yield event


def _verdict_line(result: CheckResult) -> str:
    line = result.first_wrong_line if result.first_wrong_line is not None else "ไม่มี"
    error = result.error_type or "ไม่มี"
    return f"(ผลตรวจ) verdict {result.verdict} · บรรทัดผิด {line} · {error}"


def problem_line(pending: PendingProblem) -> str:
    """How a problem card reads in the remembered conversation (§2 E item 2)."""
    return f"(โจทย์) {pending.problem.text}"


def problem_event(pending: PendingProblem) -> ProblemEvent:
    """The problem card, never with the reference (api.md "SSE events" problem)."""
    return ProblemEvent(
        problem_id=pending.problem_id,
        text_latex=pending.text_latex,
        difficulty=pending.difficulty,
        purpose="practice",
    )
