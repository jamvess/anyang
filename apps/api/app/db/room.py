"""The tutor room in Supabase: sessions, messages and the names in the room header, read and
written with the user's JWT so RLS decides what they see (specs/features/tutor/
room-sessions-db.md · apps/api/CLAUDE.md "Database").

The router depends on the `RoomRepository` protocol through `get_room_repository`, so unit tests
swap in a fake. A row RLS hides is "not there" (None), which the router answers with 404. Any
failure to reach or use the database becomes `DbUnavailableError` (503 db_unavailable).
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from supabase import Client

from app.auth import AuthContext, get_auth, get_user_db
from app.db.errors import unavailable
from app.domain.room import BuddyFacts

_SESSION_COLUMNS = "id,exam_prep_id,started_at,ended_at"
_MESSAGE_COLUMNS = "id,role,content,card,input_mode,attachment_path,attachment_name,created_at"


@dataclass(frozen=True)
class PrepRecord:
    id: UUID
    title: str
    exam_date: date
    active_scope_version_id: UUID | None


@dataclass(frozen=True)
class SessionRecord:
    id: UUID
    exam_prep_id: UUID
    started_at: datetime
    ended_at: datetime | None


@dataclass(frozen=True)
class MessageRecord:
    id: UUID
    role: str
    content: str | None
    card: Mapping[str, Any] | None
    input_mode: str | None
    attachment_path: str | None
    attachment_name: str | None
    created_at: datetime


@dataclass(frozen=True)
class ProfileFacts:
    """What the room header needs from the user's profile rows (spec §2.5)."""

    nickname: str | None
    tutor_params: Mapping[str, Any] | None
    buddy: BuddyFacts | None


class RoomRepository(Protocol):
    def get_prep(self, prep_id: UUID) -> PrepRecord | None: ...

    def create_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_prep_id: UUID,
        scope_version_id: UUID | None,
    ) -> SessionRecord: ...

    def latest_open_session(self, prep_id: UUID) -> SessionRecord | None: ...

    def get_session(self, session_id: UUID) -> SessionRecord | None: ...

    def list_messages(self, session_id: UUID) -> list[MessageRecord]:
        """Oldest first."""
        ...

    def add_message(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        role: str,
        content: str,
        input_mode: str | None,
    ) -> MessageRecord: ...

    def profile_facts(self) -> ProfileFacts: ...


def _uuid(value: str | None) -> UUID | None:
    return UUID(value) if value else None


def _prep(row: dict[str, Any]) -> PrepRecord:
    return PrepRecord(
        id=UUID(row["id"]),
        title=row["title"],
        exam_date=date.fromisoformat(row["exam_date"]),
        active_scope_version_id=_uuid(row["active_scope_version_id"]),
    )


def _session(row: dict[str, Any]) -> SessionRecord:
    ended = row["ended_at"]
    return SessionRecord(
        id=UUID(row["id"]),
        exam_prep_id=UUID(row["exam_prep_id"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        ended_at=datetime.fromisoformat(ended) if ended else None,
    )


def _message(row: dict[str, Any]) -> MessageRecord:
    return MessageRecord(
        id=UUID(row["id"]),
        role=row["role"],
        content=row["content"],
        card=row["card"],
        input_mode=row["input_mode"],
        attachment_path=row["attachment_path"],
        attachment_name=row["attachment_name"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _first[T](rows: list[dict[str, Any]], build: Callable[[dict[str, Any]], T]) -> T | None:
    return build(rows[0]) if rows else None


class SupabaseRoomRepository:
    """`connect` builds the user's client on the first query, not when the dependency resolves:
    room endpoints that never touch the DB with a token (an image message, a body that fails
    validation) must not need Supabase settings, and a client that cannot be built is a 503
    db_unavailable like any other failure, not a 500 (CI run 43152239753)."""

    def __init__(self, connect: Callable[[], Client]) -> None:
        self._connect = connect
        self._client: Client | None = None

    @property
    def _db(self) -> Client:
        if self._client is None:
            self._client = self._connect()
        return self._client

    def _run[T](self, what: str, query: Callable[[], T]) -> T:
        try:
            return query()
        except Exception as error:
            raise unavailable(what, error) from error

    def get_prep(self, prep_id: UUID) -> PrepRecord | None:
        return self._run(
            "exam_preps select",
            lambda: _first(
                self._db.table("exam_preps")
                .select("id,title,exam_date,active_scope_version_id")
                .eq("id", str(prep_id))
                .limit(1)
                .execute()
                .data,
                _prep,
            ),
        )

    def create_session(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_prep_id: UUID,
        scope_version_id: UUID | None,
    ) -> SessionRecord:
        row = {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "exam_prep_id": str(exam_prep_id),
            "scope_version_id": str(scope_version_id) if scope_version_id else None,
        }
        return self._run(
            "tutor_sessions insert",
            lambda: _session(self._db.table("tutor_sessions").insert(row).execute().data[0]),
        )

    def latest_open_session(self, prep_id: UUID) -> SessionRecord | None:
        return self._run(
            "tutor_sessions select",
            lambda: _first(
                self._db.table("tutor_sessions")
                .select(_SESSION_COLUMNS)
                .eq("exam_prep_id", str(prep_id))
                .is_("ended_at", "null")
                .order("started_at", desc=True)
                .limit(1)
                .execute()
                .data,
                _session,
            ),
        )

    def get_session(self, session_id: UUID) -> SessionRecord | None:
        return self._run(
            "tutor_sessions select",
            lambda: _first(
                self._db.table("tutor_sessions")
                .select(_SESSION_COLUMNS)
                .eq("id", str(session_id))
                .limit(1)
                .execute()
                .data,
                _session,
            ),
        )

    def list_messages(self, session_id: UUID) -> list[MessageRecord]:
        return self._run(
            "messages select",
            lambda: [
                _message(row)
                for row in self._db.table("messages")
                .select(_MESSAGE_COLUMNS)
                .eq("session_id", str(session_id))
                .order("created_at")
                .execute()
                .data
            ],
        )

    def add_message(
        self,
        *,
        tenant_id: UUID,
        session_id: UUID,
        role: str,
        content: str,
        input_mode: str | None,
    ) -> MessageRecord:
        row = {
            "tenant_id": str(tenant_id),
            "session_id": str(session_id),
            "role": role,
            "content": content,
            "input_mode": input_mode,
        }
        return self._run(
            "messages insert",
            lambda: _message(self._db.table("messages").insert(row).execute().data[0]),
        )

    def profile_facts(self) -> ProfileFacts:
        def latest(table: str, columns: str) -> dict[str, Any] | None:
            # The highest version, the newest when two rows share one (spec §2.5).
            return _first(
                self._db.table(table)
                .select(columns)
                .order("version", desc=True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data,
                dict,
            )

        def query() -> ProfileFacts:
            profile = _first(
                self._db.table("profiles").select("nickname").limit(1).execute().data, dict
            )
            tutor = latest("tutor_profiles", "params")
            buddy = latest("buddy_profiles", "enabled,params")
            return ProfileFacts(
                nickname=profile["nickname"] if profile else None,
                tutor_params=tutor["params"] if tutor else None,
                buddy=(
                    BuddyFacts(enabled=buddy["enabled"], params=buddy["params"]) if buddy else None
                ),
            )

        return self._run("profiles select", query)


def get_room_repository(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> RoomRepository | None:
    """The repository for this user, or None without a user (the router keeps the stub)."""
    if auth is None:
        return None
    return SupabaseRoomRepository(lambda: get_user_db(auth))
