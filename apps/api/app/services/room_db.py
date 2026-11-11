"""The tutor room on the database (specs/features/tutor/room-sessions-db.md · api.md v1.15).

Used by the room router when the request has a user (a token). The router checks the prep or
session before any stream starts (404, 409, 503); the generators here run inside the SSE stream,
so a failure to save there ends in `done` without that id and a log line, never an HTTP error.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import aclosing
from datetime import date
from uuid import UUID

from starlette.concurrency import run_in_threadpool

from app import stubs
from app.ai.call_context import AICallContext
from app.ai.gateway import Gateway
from app.auth import AuthContext
from app.db.errors import DbUnavailableError
from app.db.room import MessageRecord, PrepRecord, ProfileFacts, RoomRepository, SessionRecord
from app.domain.exam_prep import days_left
from app.domain.room import (
    FALLBACK_USER_NAME,
    RoomNames,
    greeting_text,
    recent_turns,
    room_names,
)
from app.models.room import DoneEvent, Limits, Message, Room, SessionEvent, TokenEvent
from app.request_context import get_request_id
from app.services.room_state import STUDENT, TUTOR, conversation_text
from app.services.tutor_turn import NO_PROBLEM, Event, reply_events
from app.settings import get_settings

log = logging.getLogger(__name__)

# How saved roles read in the tutor_reply conversation (demo-room.md §2 E item 2).
_SPEAKERS = {"user": STUDENT, "tutor": TUTOR}


def preset_tutor_name() -> str:
    """The first tutor preset of GET /personas/presets (api.md v1.15 · presets are still the
    stub's until v1.12 รอตัดสิน 5 decides where they live)."""
    return stubs.personas()["presets"]["tutors"][0]["params"]["name"]


def names_of(profile: ProfileFacts) -> RoomNames:
    return room_names(
        nickname=profile.nickname,
        tutor_params=profile.tutor_params,
        buddy=profile.buddy,
        preset_tutor_name=preset_tutor_name(),
    )


def message_of(record: MessageRecord) -> Message:
    return Message(
        id=str(record.id),
        role=record.role,  # type: ignore[arg-type]  # the messages.role check constraint
        content=record.content,
        card=dict(record.card) if record.card is not None else None,
        input_mode=record.input_mode,  # type: ignore[arg-type]
        attachment_path=record.attachment_path,
        attachment_name=record.attachment_name,
        created_at=record.created_at,
    )


def room_of(
    session: SessionRecord,
    prep: PrepRecord,
    profile: ProfileFacts,
    messages: list[MessageRecord],
    today: date,
) -> Room:
    """GET /sessions/{id} (spec §2.5)."""
    names = names_of(profile)
    guards = get_settings().ai.guards
    return Room(
        session_id=session.id,
        prep_name=prep.title,
        days_left=days_left(prep.exam_date, today=today),
        user_name=names.user_name,
        tutor_name=names.tutor_name,
        buddy_name=names.buddy_name,
        limits=Limits(max_message_chars=guards.max_message_chars, max_image_mb=guards.max_image_mb),
        messages=[message_of(m) for m in messages],
    )


def greeting_of(prep: PrepRecord, profile: ProfileFacts, today: date) -> str:
    """Spec §2.8: the template from config/messages.yaml; no AI call."""
    user_name = names_of(profile).user_name
    return greeting_text(
        get_settings().messages.room_greeting,
        user_name=None if user_name == FALLBACK_USER_NAME else user_name,
        prep_name=prep.title,
        days_left=days_left(prep.exam_date, today=today),
    )


async def _save_tutor(
    repo: RoomRepository, auth: AuthContext, session: SessionRecord, text: str
) -> list[UUID]:
    """The id of the saved tutor message, or [] when it could not be saved (logged by
    `unavailable` with the request id · spec AC-5, AC-18). In the thread pool: the client
    blocks."""
    try:
        record = await run_in_threadpool(
            lambda: repo.add_message(
                tenant_id=auth.tenant_id,
                session_id=session.id,
                role="tutor",
                content=text,
                input_mode=None,
            )
        )
    except DbUnavailableError:
        # The reply is on screen but will be gone after a reload: worth a line with the request.
        log.warning(
            "tutor message not saved (request_id=%s, session_id=%s)", get_request_id(), session.id
        )
        return []
    return [record.id]


async def opening_events(
    repo: RoomRepository, auth: AuthContext, session: SessionRecord, greeting: str
) -> AsyncIterator[Event]:
    """Spec §2.4: session → token (the greeting) → done. No progress_card and no problem."""
    yield "session", SessionEvent(session_id=session.id)
    yield "token", TokenEvent(speaker="tutor", text=greeting)
    ids = await _save_tutor(repo, auth, session, greeting)
    yield "done", DoneEvent(message_ids=ids)


def conversation_of(messages: list[MessageRecord]) -> str:
    """Spec §2.7 item 3: the last `session.context_recent_turns` turns, escaped."""
    lines = [(m.role, m.content) for m in messages if m.role in _SPEAKERS and m.content is not None]
    turns = get_settings().learning.session.context_recent_turns
    return conversation_text([(_SPEAKERS[role], text) for role, text in recent_turns(lines, turns)])


async def reply_and_save(
    gateway: Gateway,
    repo: RoomRepository,
    auth: AuthContext,
    session: SessionRecord,
    text: str,
    conversation: str,
) -> AsyncIterator[Event]:
    """Spec §2.7 items 5-7: tutor_reply with no problem and the saved conversation. A finished
    reply, the degrade text included, is saved before `done`; a reply cut by `error` is not."""
    call_context = AICallContext(auth.tenant_id, auth.user_id, session.id)
    said: list[str] = []
    async with aclosing(
        reply_events(gateway, text, call_context, NO_PROBLEM, conversation)
    ) as events:
        async for name, payload in events:
            if name == "token" and isinstance(payload, TokenEvent):
                said.append(payload.text)
            if name == "done":
                ids = await _save_tutor(repo, auth, session, "".join(said))
                yield "done", DoneEvent(message_ids=ids)
            else:
                yield name, payload
