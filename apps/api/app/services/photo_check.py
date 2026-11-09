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
from app.domain.checker import CheckResult, working_missing
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


def _check_result_text(result: CheckResult, no_working: bool = False) -> str:
    fields = {
        "verdict": result.verdict,
        "first_wrong_line": result.first_wrong_line,
        "error_type": result.error_type,
        "evidence": result.evidence,
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
    """After a check, photo or typed (spec §2.2 items 5-8 · demo-room §2 B, D, E): mastery,
    verdict, the tutor's explanation, then the demo's next problem.

    A right answer with no working (demo-room §2 I) gets none of these but the explanation,
    which asks for the working: no verdict, no attempt, the same problem stays."""
    problem = pending.problem
    no_working = working_missing(result.verdict, len(lines), get_settings().learning.checker)
    if no_working:
        await state.remember(key, TUTOR, NO_WORKING_LINE)
    else:
        await state.record_check(key, pending, result.is_correct)  # demo: BKT (§2 D)
        await state.remember(key, TUTOR, _verdict_line(result))
        yield "verdict", verdict
    explain_input = {
        "problem": problem.text,
        # Sent on purpose: the tutor shows the right value and method (§2.2.4). This problem
        # is already answered, so AM-13 does not apply.
        "reference_answer": problem.reference_answer,
        "solution_steps": solution_steps_text(problem),
        "answer_lines": number_lines(lines),
        "check_result": _check_result_text(result, no_working),
    }

    async def after_explaining(explanation: str) -> AsyncIterator[Event]:
        # Runs only when the explanation finished (tutor_events), so a degrade text is never
        # remembered as the tutor speaking (§2 E item 2).
        await state.remember(key, TUTOR, explanation)
        if no_working:
            return  # the same problem stays, so no next problem
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
