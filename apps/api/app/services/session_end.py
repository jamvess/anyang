"""Ending the session with a token (specs/features/tutor/session-end-db.md · api.md v1.9).

The router has already closed the session (one conditional update, before any AI call). Here:
the result of the session by code (`app/domain/room.py`), the summary by `session_summary`
(code decides, the LLM speaks · CLAUDE.md rule 1), saved, then `session_end` → `done`. Store
calls run in the thread pool: the Supabase client blocks.
"""

import asyncio
import logging
import re
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
_NUMBER = re.compile(r"\d+")


async def _result(
    problems: ProblemRepository | None, session: SessionRecord
) -> SessionResult | None:
    """§2.2. No problem repository = no answers to count; a read that fails = None (unknown),
    so the summary never says "nothing answered" when it could not look (self-review)."""
    if problems is None:
        return SessionResult([], 0, 0)
    try:
        # Three reads at once: they run before the AI call (self-review PR #136).
        answers, topics, progress = await asyncio.gather(
            run_in_threadpool(problems.attempts_since, session.started_at),
            run_in_threadpool(problems.list_topics, session.exam_prep_id),
            run_in_threadpool(problems.list_progress, session.exam_prep_id),
        )
    except DbUnavailableError:
        log.warning("session result not read (request_id=%s)", get_request_id())
        return None
    return session_result(
        [(a.topic_id, a.is_correct) for a in answers],
        topics,
        {p.topic_id: p.level for p in progress},
    )


def _fallback(result: SessionResult | None) -> list[str]:
    """§2.3 item 3: the templates of config/messages.yaml when the AI cannot be used."""
    room = get_settings().messages.room
    if result is None:
        return [room.session_summary_unknown]
    if result.answers == 0:
        return [room.session_summary_empty]
    return [room.session_summary_answered.format(answers=result.answers, right=result.right)]


def _numbers_from_facts(lines: list[str], values: dict[str, str]) -> bool:
    """§2.3 item 2: every number the summary says is a number of the facts (code decides the
    counts; a summary that makes one up is not shown · self-review PR #136)."""
    allowed = set(_NUMBER.findall(" ".join(values.values())))
    return all(n in allowed for line in lines for n in _NUMBER.findall(line))


async def _summary(
    gateway: Gateway, values: dict[str, str], call_context: AICallContext
) -> list[str] | None:
    try:
        with call_scope(call_context):
            summary = await gateway.call("session_summary", values, SessionSummaryResult)
    except Exception:  # the model, the schema after retries, anything: the session is over
        log.warning("session_summary failed; the template stands in", exc_info=True)
        return None
    lines = list(summary.lines)
    if not _numbers_from_facts(lines, values):
        log.warning("session_summary says a number that is not in the facts: %r", lines)
        return None
    return lines


async def end_events(
    gateway: Gateway,
    repo: RoomRepository,
    problems: ProblemRepository | None,
    auth: AuthContext,
    session: SessionRecord,
    prep: PrepRecord,
    days: int,
) -> AsyncIterator[Event]:
    """§2.3-2.4: the summary is saved (summary + a tutor message) before `session_end`, so a
    client that leaves on that event still finds it after a reload (self-review)."""
    result = await _result(problems, session)
    lines = None
    if result is not None:
        values = {
            "prep_name": prep.title,
            "days_left": str(days),
            "topics": topics_text(result) or NONE,
            "totals": totals_text(result),
        }
        call_context = AICallContext(auth.tenant_id, auth.user_id, session.id)
        lines = await _summary(gateway, values, call_context)
    lines = lines or _fallback(result)

    text = "\n".join(lines)
    try:
        await run_in_threadpool(repo.save_summary, session.id, text)
    except DbUnavailableError:
        log.warning(
            "session summary not saved (request_id=%s, session_id=%s)", get_request_id(), session.id
        )
    ids = await _save_tutor(repo, auth, session, text)  # PM-05: a chat message (api.md v1.9)
    yield "session_end", SessionEndEvent(summary_lines=lines)
    yield "done", DoneEvent(message_ids=ids)
