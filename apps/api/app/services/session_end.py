"""Ending the session with a token (specs/features/tutor/session-end-db.md · api.md v1.9).

The router has already closed the session (one conditional update, before any AI call). Here:
the result of the session by code (`app/domain/room.py`), the summary by `session_summary`
(code decides, the LLM speaks · CLAUDE.md rule 1), then `session_end` → saved → `done`. Store
calls run in the thread pool: the Supabase client blocks.
"""

import logging
from collections.abc import AsyncIterator

from starlette.concurrency import run_in_threadpool

from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.auth import AuthContext
from app.db.errors import DbUnavailableError
from app.db.room import PrepRecord, RoomRepository, SessionRecord
from app.db.room_problems import ProblemRepository
from app.domain.room import SessionResult, session_result, topics_text, totals_text
from app.models.room import DoneEvent, SessionEndEvent
from app.models.tutor_ai import SessionSummaryResult
from app.request_context import get_request_id
from app.services.room_db import _save_tutor
from app.services.tutor_turn import Event, call_scope
from app.settings import get_settings

log = logging.getLogger(__name__)

NONE = "none"  # the prompts' word for "nothing"


async def _result(problems: ProblemRepository | None, session: SessionRecord) -> SessionResult:
    """§2.2: no problem repository, or a read that fails, gives a session with no answers."""
    if problems is None:
        return SessionResult([], 0, 0)
    try:
        answers = await run_in_threadpool(problems.attempts_since, session.started_at)
        topics = await run_in_threadpool(problems.list_topics, session.exam_prep_id)
        progress = await run_in_threadpool(problems.list_progress, session.exam_prep_id)
    except DbUnavailableError:
        log.warning("session result not read (request_id=%s)", get_request_id())
        return SessionResult([], 0, 0)
    return session_result(
        [(a.topic_id, a.is_correct) for a in answers],
        topics,
        {p.topic_id: p.level for p in progress},
    )


def _fallback(result: SessionResult) -> list[str]:
    """§2.3 item 3: the template of config/messages.yaml when the AI fails."""
    room = get_settings().messages.room
    if result.answers == 0:
        return [room.session_summary_empty]
    return [room.session_summary_answered.format(answers=result.answers, right=result.right)]


async def end_events(
    gateway: Gateway,
    repo: RoomRepository,
    problems: ProblemRepository | None,
    auth: AuthContext,
    session: SessionRecord,
    prep: PrepRecord,
    days: int,
) -> AsyncIterator[Event]:
    """§2.3-2.4: session_end → saved (summary + a tutor message) → done."""
    result = await _result(problems, session)
    values = {
        "prep_name": prep.title,
        "days_left": str(days),
        "topics": topics_text(result) or NONE,
        "totals": totals_text(result),
    }
    try:
        with call_scope(AICallContext(auth.tenant_id, auth.user_id, session.id)):
            summary = await gateway.call("session_summary", values, SessionSummaryResult)
        lines = list(summary.lines)
    except Exception:  # the model, the schema after retries, anything: the session is over
        log.warning("session_summary failed; the template stands in", exc_info=True)
        lines = _fallback(result)
    yield "session_end", SessionEndEvent(summary_lines=lines)

    text = "\n".join(lines)
    try:
        await run_in_threadpool(repo.save_summary, session.id, text)
    except DbUnavailableError:
        log.warning(
            "session summary not saved (request_id=%s, session_id=%s)", get_request_id(), session.id
        )
    ids = await _save_tutor(repo, auth, session, text)  # PM-05: a chat message (api.md v1.9)
    yield "done", DoneEvent(message_ids=ids)
