"""What the room reads and writes to pick a topic and give a problem
(specs/features/tutor/room-problems-db.md §2.1 to §2.4 · data-model.md รูป 2-3).

Read and written with the user's JWT, so RLS decides (apps/api/CLAUDE.md "Database"). A second
repository next to `RoomRepository` (#123): `get_problem_repository` gives one only when the room
repository is the Supabase one, so tests that fake only the room keep the room as it was.
Any failure to reach or use the database becomes `DbUnavailableError`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from supabase import Client

from app.auth import AuthContext, get_auth
from app.db.errors import DbUnavailableError, unavailable
from app.db.room import RoomRepository, SupabaseRoomRepository, get_room_repository
from app.domain.room import TopicFacts

__all__ = [
    "DbUnavailableError",
    "ProblemRecord",
    "ProblemRepository",
    "ProgressFacts",
    "SkillFacts",
    "SupabaseProblemRepository",
    "get_problem_repository",
]


@dataclass(frozen=True)
class ProgressFacts:
    """The user's `topic_progress` row of a topic. `d_max` has no column yet (spec §10 item 2):
    None until step 8 adds it."""

    topic_id: UUID
    mastery: float
    attempts_n: int
    level: str
    d_max: int | None = None


@dataclass(frozen=True)
class SkillFacts:
    id: UUID
    name: str


@dataclass(frozen=True)
class ProblemRecord:
    id: UUID
    session_id: UUID
    topic_id: UUID
    skill_id: UUID | None
    text: str
    reference_answer: str
    solution_steps: list[str]
    answer_format: str
    difficulty: int
    purpose: str


class ProblemRepository(Protocol):
    def list_topics(self, prep_id: UUID) -> list[TopicFacts]:
        """All topics of the prep, by `order_index` (the caller leaves out excluded ones)."""
        ...

    def list_progress(self, prep_id: UUID) -> list[ProgressFacts]: ...
    def list_skills(self, topic_id: UUID) -> list[SkillFacts]:
        """Skills that are not excluded."""
        ...

    def source_chunks(self, topic_id: UUID, limit: int) -> list[str]:
        """Text of up to ``limit`` chunks whose pages overlap the topic's sources, by file and
        page."""
        ...

    def open_problem(self, prep_id: UUID, topic_id: UUID) -> ProblemRecord | None:
        """The latest problem of the topic in this prep with no attempt."""
        ...

    def session_problem(self, session_id: UUID) -> ProblemRecord | None:
        """The problem on screen in this session: the latest problem with no attempt of the
        session's prep, since a reopened room shows an open problem of an earlier session
        (AC-8 · self-review PR #131)."""
        ...

    def topic_has_problems(self, prep_id: UUID, topic_id: UUID) -> bool: ...
    def add_problem(self, **fields: Any) -> ProblemRecord:
        """Insert a `problems` row from its columns; the saved row."""
        ...


def _uuid(value: Any) -> UUID | None:
    return UUID(str(value)) if value is not None else None


def _problem(row: dict[str, Any]) -> ProblemRecord:
    return ProblemRecord(
        id=UUID(str(row["id"])),
        session_id=UUID(str(row["session_id"])),
        topic_id=UUID(str(row["topic_id"])),
        skill_id=_uuid(row.get("skill_id")),
        text=row["text"],
        reference_answer=row["reference_answer"],
        solution_steps=list(row.get("solution_steps") or []),
        answer_format=row["answer_format"],
        difficulty=int(row["difficulty"]),
        purpose=row["purpose"],
    )


def _json(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, list):
        return [_json(v) for v in value]
    return value


class SupabaseProblemRepository:
    def __init__(self, connect: Callable[[], Client]) -> None:
        self._connect = connect
        self._client: Client | None = None

    def _db(self) -> Client:
        if self._client is None:
            self._client = self._connect()
        return self._client

    def _run[T](self, what: str, query: Callable[[], T]) -> T:
        try:
            return query()
        except Exception as error:  # network, PostgREST, unexpected row shape
            raise unavailable(f"room problems {what}", error) from error

    def list_topics(self, prep_id: UUID) -> list[TopicFacts]:
        rows = self._run(
            "topics",
            lambda: (
                self._db()
                .table("topics")
                .select("id,name,order_index,importance,status,origin,signal_r")
                .eq("exam_prep_id", str(prep_id))
                .order("order_index")
                .execute()
                .data
            ),
        )
        return [
            TopicFacts(
                id=UUID(r["id"]),
                name=r["name"],
                order_index=int(r["order_index"]),
                importance=r.get("importance"),
                status=r["status"],
                origin=r["origin"],
                signal_r=float(r.get("signal_r") or 0.0),
            )
            for r in rows
        ]

    def list_progress(self, prep_id: UUID) -> list[ProgressFacts]:
        rows = self._run(
            "progress",
            lambda: (
                self._db()
                .table("topic_progress")
                .select("topic_id,mastery,attempts_n,level")
                .eq("exam_prep_id", str(prep_id))
                .execute()
                .data
            ),
        )
        return [
            ProgressFacts(
                topic_id=UUID(r["topic_id"]),
                mastery=float(r["mastery"]),
                attempts_n=int(r["attempts_n"]),
                level=r["level"],
            )
            for r in rows
        ]

    def list_skills(self, topic_id: UUID) -> list[SkillFacts]:
        rows = self._run(
            "skills",
            lambda: (
                self._db()
                .table("topic_skills")
                .select("id,name")
                .eq("topic_id", str(topic_id))
                .eq("excluded", False)
                .order("name")
                .execute()
                .data
            ),
        )
        return [SkillFacts(id=UUID(r["id"]), name=r["name"]) for r in rows]

    def source_chunks(self, topic_id: UUID, limit: int) -> list[str]:
        def query() -> list[str]:
            sources = (
                self._db()
                .table("topic_sources")
                .select("material_id,page_from,page_to")
                .eq("topic_id", str(topic_id))
                .order("material_id")
                .order("page_from")
                .execute()
                .data
            )
            texts: list[str] = []
            seen: set[str] = set()  # overlapping sources must not repeat a chunk
            for source in sources:
                if len(texts) >= limit:
                    break
                chunks = (
                    self._db()
                    .table("chunks")
                    .select("id,text")
                    .eq("material_id", source["material_id"])
                    .lte("page_from", source["page_to"])
                    .gte("page_to", source["page_from"])
                    .order("page_from")
                    .limit(limit)
                    .execute()
                    .data
                )
                for chunk in chunks:
                    if chunk["id"] not in seen and len(texts) < limit:
                        seen.add(chunk["id"])
                        texts.append(chunk["text"])
            return texts[:limit]

        return self._run("source chunks", query)

    def _without_attempts(self, rows: list[dict[str, Any]]) -> ProblemRecord | None:
        if not rows:
            return None
        ids = [r["id"] for r in rows]
        answered = {
            a["problem_id"]
            for a in self._db()
            .table("attempts")
            .select("problem_id")
            .in_("problem_id", ids)
            .execute()
            .data
        }
        for row in rows:  # newest first
            if row["id"] not in answered:
                return _problem(row)
        return None

    def open_problem(self, prep_id: UUID, topic_id: UUID) -> ProblemRecord | None:
        def query() -> ProblemRecord | None:
            rows = (
                self._db()
                .table("problems")
                .select("*")
                .eq("topic_id", str(topic_id))
                .order("created_at", desc=True)
                .execute()
                .data
            )
            return self._without_attempts(rows)

        return self._run("open problem", query)

    def session_problem(self, session_id: UUID) -> ProblemRecord | None:
        def query() -> ProblemRecord | None:
            session = (
                self._db()
                .table("tutor_sessions")
                .select("exam_prep_id")
                .eq("id", str(session_id))
                .execute()
                .data
            )
            if not session:
                return None
            sessions = (
                self._db()
                .table("tutor_sessions")
                .select("id")
                .eq("exam_prep_id", session[0]["exam_prep_id"])
                .execute()
                .data
            )
            rows = (
                self._db()
                .table("problems")
                .select("*")
                .in_("session_id", [s["id"] for s in sessions])
                .order("created_at", desc=True)
                .execute()
                .data
            )
            return self._without_attempts(rows)

        return self._run("session problem", query)

    def topic_has_problems(self, prep_id: UUID, topic_id: UUID) -> bool:
        rows = self._run(
            "topic problems",
            lambda: (
                self._db()
                .table("problems")
                .select("id")
                .eq("topic_id", str(topic_id))
                .limit(1)
                .execute()
                .data
            ),
        )
        return bool(rows)

    def add_problem(self, **fields: Any) -> ProblemRecord:
        rows = self._run(
            "insert problem",
            lambda: (
                self._db()
                .table("problems")
                .insert({k: _json(v) for k, v in fields.items()})
                .execute()
                .data
            ),
        )
        return _problem(rows[0])


def get_problem_repository(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    room: Annotated[RoomRepository | None, Depends(get_room_repository)],
) -> "ProblemRepository | None":
    """With a user and the Supabase room repository; None otherwise (spec §2.1 item 2: the room
    opens as before)."""
    if auth is None or not isinstance(room, SupabaseRoomRepository):
        return None
    return SupabaseProblemRepository(room.client)
