"""A photo answer in the room: extract_answer → ocr_preview, then confirm → checker → verdict →
explain_check (specs/features/check/photo-check-in-room.md).

P1 (``extract_answer``) reads the handwriting; P2 (``check_answer`` service: SymPy + classifier
+ merge rules) checks the lines the user confirmed; ``explain_check`` turns the result into the
tutor's explanation (AM-07). Code decides, the LLM speaks (CLAUDE.md rule 1). Storage and the
database come later (spec §9): the image is read through ``ImageStore`` and the pending problem
and preview live in ``RoomState`` (app/services/room_state.py).
"""

import json
import logging
from collections.abc import AsyncIterator, Sequence
from contextlib import aclosing, nullcontext
from typing import Any, Protocol

from pydantic import BaseModel

from app.ai.call_context import AICallContext, ai_call_context
from app.ai.gateway import AIProviderError, AISchemaError, Gateway, Image
from app.domain.checker import CheckResult
from app.models.room import DoneEvent, OcrLine, OcrPreviewEvent, TokenEvent, VerdictEvent
from app.models.scope_ai import ExtractAnswerResult
from app.services.checker import check_answer, number_lines, solution_steps_text
from app.services.room_state import PendingPreview, PendingProblem, RoomState
from app.services.tutor_turn import DEGRADE_TEXT, INTERNAL_ERROR, tutor_events

log = logging.getLogger(__name__)
# AM-03: which lines the user corrected on the card (spec §2.2 item 3) · Cloud Logging for now.
confirm_log = logging.getLogger("app.ocr.confirm")

# Tutor lines that come from code, not from a model (spec §2.1).
LOOKING = "ขอดูก่อนนะ"
CHECK_PLEASE = "เช็คให้หน่อยว่าอ่านถูกไหม"
UNREADABLE = "รูปนี้อ่านไม่ออก ลองถ่ายใหม่ให้ชัดขึ้นอีกนิดนะ"
# UC-04 E9 with no intent router yet (spec §10 item 4 · proposal pending Junior).
NO_PENDING_PROBLEM = "ตอนนี้ยังไม่มีโจทย์ที่รอคำตอบ ส่งคำถามเป็นข้อความได้เลยนะ"

Event = tuple[str, BaseModel]


class ImageStore(Protocol):
    async def read(self, path: str) -> Image | None:
        """The uploaded file at ``path``, or None when there is none."""
        ...


def get_image_store() -> ImageStore | None:
    """FastAPI dependency. None means no Storage yet (spec §2.4): photo messages and
    ocr/confirm keep their stubs until Junior wires Supabase Storage and the real /uploads."""
    return None


def _context(call_context: AICallContext | None) -> Any:
    if call_context is None:
        return nullcontext()
    return ai_call_context(
        tenant_id=call_context.tenant_id,
        user_id=call_context.user_id,
        session_id=call_context.session_id,
    )


def _tutor(text: str) -> Event:
    return "token", TokenEvent(speaker="tutor", text=text)


async def photo_events(
    gateway: Gateway,
    state: RoomState,
    session_id: str,
    pending: PendingProblem,
    image: Image,
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    """SSE of a photo message (spec §2.1 items 4-6). The caption never reaches the model."""
    yield _tutor(LOOKING)  # before the model call, so the user sees the photo was taken
    try:
        with _context(call_context):
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

    if not result.lines:  # unreadable or not an answer (UC-04 E1); the old preview stays
        yield _tutor(UNREADABLE)
        yield "done", DoneEvent()
        return
    lines = [OcrLine(latex=line.latex, confidence=line.confidence) for line in result.lines]
    # Confirmed every time, whatever the confidence (AM-02 · ocr.always_confirm, P1).
    await state.set_preview(
        session_id, PendingPreview(pending=pending, lines=tuple(line.latex for line in lines))
    )
    yield "ocr_preview", OcrPreviewEvent(lines=lines)
    yield _tutor(CHECK_PLEASE)
    yield "done", DoneEvent()


def _check_result_text(result: CheckResult) -> str:
    fields = {
        "verdict": result.verdict,
        "first_wrong_line": result.first_wrong_line,
        "error_type": result.error_type,
        "evidence": result.evidence,
        "method": result.method,
    }
    return "\n".join(f"{name}: {'none' if v is None else v}" for name, v in fields.items())


def _log_edits(session_id: str, preview: PendingPreview, lines: Sequence[str]) -> None:
    edited = [
        n for n, (old, new) in enumerate(zip(preview.lines, lines, strict=True), 1) if old != new
    ]
    confirm_log.info(
        json.dumps({"session_id": session_id, "line_count": len(lines), "edited_lines": edited})
    )


async def confirm_events(
    gateway: Gateway,
    state: RoomState,
    session_id: str,
    preview: PendingPreview,
    lines: list[str],
    call_context: AICallContext | None = None,
) -> AsyncIterator[Event]:
    """SSE of ocr/confirm (spec §2.2 items 3-8): verdict first, then the tutor explains."""
    problem = preview.pending.problem
    try:
        with _context(call_context):
            result = await check_answer(problem, lines, gateway=gateway)
    except (AIProviderError, AISchemaError):
        # Temporary instead of UC-04 E4 (spec §10 item 2): no verdict, confirm again.
        log.warning("check_answer classifier failed; the preview stays to confirm again")
        yield _tutor(DEGRADE_TEXT)
        yield "done", DoneEvent()
        return
    except Exception:
        log.exception("check_answer failed")
        yield "error", INTERNAL_ERROR
        return

    await state.clear_preview(session_id)  # one confirm per preview
    _log_edits(session_id, preview, lines)
    yield (
        "verdict",
        VerdictEvent(
            verdict=result.verdict,
            first_wrong_line=result.first_wrong_line,
            error_type=result.error_type,
        ),
    )
    explain_input = {
        "problem": problem.text,
        # Sent on purpose: the tutor shows the right value and method (§2.2.4). This problem
        # is already answered, so AM-13 does not apply.
        "reference_answer": problem.reference_answer,
        "solution_steps": solution_steps_text(problem),
        "answer_lines": number_lines(lines),
        "check_result": _check_result_text(result),
    }
    async with aclosing(
        tutor_events(gateway, "explain_check", explain_input, call_context)
    ) as events:
        async for event in events:
            yield event
