"""What the room reads and writes to pick a topic and give a problem
(specs/features/tutor/room-problems-db.md §2.1 to §2.4 · data-model.md รูป 2-3).

Read and written with the user's JWT, so RLS decides (apps/api/CLAUDE.md "Database"). A second
repository next to `RoomRepository` (#123): `get_problem_repository` gives one only when the room
repository is the Supabase one, so tests that fake only the room keep the room as it was.
Any failure to reach or use the database becomes `DbUnavailableError`.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from postgrest.types import CountMethod
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
    """The user's `topic_progress` row of a topic (`d_max` since migration 0007 ·
    topic-progress-db.md §5)."""

    topic_id: UUID
    mastery: float
    attempts_n: int
    level: str
    d_max: int = 0
    correct_n: int = 0


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
    def get_topic_progress(self, topic_id: UUID) -> ProgressFacts | None:
        """The user's row of the topic, or None (topic-progress-db.md §2.2 item 1)."""
        ...

    def save_topic_progress(self, **fields: Any) -> None:
        """Upsert the user's row by (user_id, topic_id) with these columns (§2.3 item 1)."""
        ...

    def list_skills(self, topic_id: UUID) -> list[SkillFacts]:
        """Skills that are not excluded."""
        ...

    def source_chunks(self, topic_id: UUID, limit: int) -> list[str]:
        """Text of up to ``limit`` chunks whose pages overlap the topic's sources, by file and
        page."""
        ...

    def open_problem(self, prep_id: UUID, topic_id: UUID) -> ProblemRecord | None:
        """The latest problem of the topic in this prep that has not ended (`ended_at` null ·
        room-answers-db.md §2.2 item 1)."""
        ...

    def session_problem(self, session_id: UUID) -> ProblemRecord | None:
        """The problem on screen in this session: the latest problem of the session's prep that
        has not ended, since a reopened room shows an open problem of an earlier session
        (AC-8 · self-review PR #131)."""
        ...

    def topic_has_problems(self, prep_id: UUID, topic_id: UUID) -> bool: ...
    def recent_problems(self, prep_id: UUID, topic_id: UUID, limit: int) -> list[ProblemRecord]:
        """Up to ``limit`` problems of the topic in this prep, newest first, ended or not
        (§2.3 item 2 · v2)."""
        ...

    def add_problem(self, **fields: Any) -> ProblemRecord:
        """Insert a `problems` row from its columns; the saved row."""
        ...

    # What an answer writes (room-answers-db.md §2.2 items 2-5, §2.3).

    def add_attempt(self, **fields: Any) -> None:
        """Insert an `attempts` row from its columns."""
        ...

    def count_wrong_attempts(self, problem_id: UUID) -> int:
        """`attempts` rows of the problem with `verdict = incorrect` (the hint ladder)."""
        ...

    def end_problem(self, problem_id: UUID) -> bool | None:
        """Set `ended_at` to now, once; a problem that has ended keeps its first time. True
        when this call ended it, False when it had ended already (another request won), None
        when the store cannot say (self-review PR #135)."""
        ...

    def working_steps(self, problem_id: UUID) -> int: ...
    def add_working_steps(self, problem_id: UUID, steps: int) -> None: ...


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


_PROGRESS_COLUMNS = "topic_id,mastery,attempts_n,correct_n,level,d_max"


def _progress(row: dict[str, Any]) -> ProgressFacts:
    return ProgressFacts(
        topic_id=UUID(row["topic_id"]),
        mastery=float(row["mastery"]),
        attempts_n=int(row["attempts_n"]),
        level=row["level"],
        d_max=int(row.get("d_max") or 0),
        correct_n=int(row.get("correct_n") or 0),
    )


def _json(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
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
                .select(_PROGRESS_COLUMNS)
                .eq("exam_prep_id", str(prep_id))
                .execute()
                .data
            ),
        )
        return self._run("progress rows", lambda: [_progress(r) for r in rows])

    def get_topic_progress(self, topic_id: UUID) -> ProgressFacts | None:
        rows = self._run(
            "topic progress",
            lambda: (
                self._db()
                .table("topic_progress")
                .select(_PROGRESS_COLUMNS)
                .eq("topic_id", str(topic_id))  # RLS: only the user's own row
                .execute()
                .data
            ),
        )
        # An unexpected row shape is a store failure too, so the room goes on (§2.3 item 2).
        return self._run("topic progress row", lambda: _progress(rows[0]) if rows else None)

    def save_topic_progress(self, **fields: Any) -> None:
        self._run(
            "save topic progress",
            lambda: (
                self._db()
                .table("topic_progress")
                .upsert({k: _json(v) for k, v in fields.items()}, on_conflict="user_id,topic_id")
                .execute()
            ),
        )

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

    def open_problem(self, prep_id: UUID, topic_id: UUID) -> ProblemRecord | None:
        def query() -> ProblemRecord | None:
            rows = (
                self._db()
                .table("problems")
                .select("*")
                .eq("topic_id", str(topic_id))
                .is_("ended_at", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
            )
            return _problem(rows[0]) if rows else None

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
                .is_("ended_at", "null")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
                .data
            )
            return _problem(rows[0]) if rows else None

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

    def recent_problems(self, prep_id: UUID, topic_id: UUID, limit: int) -> list[ProblemRecord]:
        if limit <= 0:
            return []
        rows = self._run(
            "recent problems",
            lambda: (
                self._db()
                .table("problems")
                .select("*")
                .eq("topic_id", str(topic_id))  # a topic belongs to one prep
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
                .data
            ),
        )
        return [_problem(row) for row in rows]

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

    def add_attempt(self, **fields: Any) -> None:
        self._run(
            "insert attempt",
            lambda: (
                self._db()
                .table("attempts")
                .insert({k: _json(v) for k, v in fields.items()})
                .execute()
            ),
        )

    def count_wrong_attempts(self, problem_id: UUID) -> int:
        count = self._run(
            "wrong attempts",
            lambda: (
                self._db()
                .table("attempts")
                .select("id", count=CountMethod.exact, head=True)  # the count, no rows
                .eq("problem_id", str(problem_id))
                .eq("verdict", "incorrect")
                .execute()
                .count
            ),
        )
        return int(count or 0)

    def end_problem(self, problem_id: UUID) -> bool | None:
        rows = self._run(
            "end problem",
            lambda: (
                self._db()
                .table("problems")
                .update({"ended_at": datetime.now(UTC).isoformat()})
                .eq("id", str(problem_id))
                .is_("ended_at", "null")
                .execute()
                .data
            ),
        )
        return bool(rows)  # PostgREST returns the updated rows: none = it had ended already

    def working_steps(self, problem_id: UUID) -> int:
        rows = self._run(
            "working steps",
            lambda: (
                self._db()
                .table("problems")
                .select("working_steps")
                .eq("id", str(problem_id))
                .execute()
                .data
            ),
        )
        return int(rows[0]["working_steps"]) if rows else 0

    def add_working_steps(self, problem_id: UUID, steps: int) -> None:
        # Read then write: one student answers one problem at a time, so two requests that add
        # steps to the same problem at once are not a case of the demo (spec §2.2 item 3).
        total = self.working_steps(problem_id) + steps
        self._run(
            "add working steps",
            lambda: (
                self._db()
                .table("problems")
                .update({"working_steps": total})
                .eq("id", str(problem_id))
                .execute()
            ),
        )


def get_problem_repository(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
    room: Annotated[RoomRepository | None, Depends(get_room_repository)],
) -> "ProblemRepository | None":
    """With a user and the Supabase room repository; None otherwise (spec §2.1 item 2: the room
    opens as before)."""
    if auth is None or not isinstance(room, SupabaseRoomRepository):
        return None
    return SupabaseProblemRepository(room.client)
