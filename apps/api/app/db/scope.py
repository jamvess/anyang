"""What the scope page reads and writes (specs/features/scope/scope-db.md · data-model.md รูป 2).

Read and written with the user's JWT, so RLS decides (apps/api/CLAUDE.md "Database"). Any failure
to reach or use the database becomes `DbUnavailableError`, except a version number that another
request took first, which is `VersionTakenError` (the unique key of `scope_versions`).
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from postgrest.exceptions import APIError
from supabase import Client

from app.auth import AuthContext, get_auth, get_user_db
from app.db.errors import DbUnavailableError, unavailable

__all__ = [
    "DbUnavailableError",
    "QuestionRow",
    "ScopePrep",
    "ScopeRepository",
    "SourceRange",
    "SupabaseScopeRepository",
    "TopicRow",
    "VersionRow",
    "VersionTakenError",
    "get_scope_repository",
]

_UNIQUE_VIOLATION = "23505"  # PostgreSQL error code


class VersionTakenError(Exception):
    """(exam_prep_id, version) exists: another request confirmed first (spec §2.3 item 4)."""


@dataclass(frozen=True)
class ScopePrep:
    id: UUID
    title: str
    exam_date: date
    active_scope_version_id: UUID | None


@dataclass(frozen=True)
class TopicRow:
    id: UUID
    exam_prep_id: UUID
    name: str
    order_index: int
    importance: int | None
    importance_reason: str | None
    status: str  # draft | confirmed | excluded
    origin: str  # doc | user


@dataclass(frozen=True)
class SourceRange:
    topic_id: UUID
    material_id: UUID
    file_name: str
    material_created_at: datetime
    page_from: int
    page_to: int


@dataclass(frozen=True)
class QuestionRow:
    id: UUID
    material_id: UUID
    file_name: str
    material_created_at: datetime
    q_no: str
    page_no: int | None
    text: str
    map_note: str | None
    topic_id: UUID | None


@dataclass(frozen=True)
class VersionRow:
    id: UUID
    version: int
    confirmed_at: datetime | None


class ScopeRepository(Protocol):
    def get_prep(self, prep_id: UUID) -> ScopePrep | None: ...
    def list_topics(self, prep_id: UUID) -> list[TopicRow]:
        """Every topic of the prep, excluded ones too, by `order_index`."""
        ...

    def list_sources(self, prep_id: UUID) -> list[SourceRange]:
        """The page ranges of the prep's topics, with the name and time of their file."""
        ...

    def list_questions(self, prep_id: UUID) -> list[QuestionRow]:
        """The past exam questions of the prep's files, mapped or not."""
        ...

    def scope_version(self, version_id: UUID) -> VersionRow | None: ...
    def has_changes_after(self, prep_id: UUID, after: datetime) -> bool:
        """A `scope_changes` row of the prep created after ``after``."""
        ...

    def latest_version(self, prep_id: UUID) -> int:
        """The highest `scope_versions.version` of the prep, 0 when there is none."""
        ...

    def add_version(self, **fields: Any) -> UUID:
        """Insert a `scope_versions` row; `VersionTakenError` when the version exists."""
        ...

    def set_active_version(self, prep_id: UUID, version_id: UUID) -> None: ...
    def confirm_topics(self, prep_id: UUID) -> None:
        """Topics of the prep with `status = 'draft'` become `'confirmed'`."""
        ...

    def get_topic(self, topic_id: UUID) -> TopicRow | None: ...
    def pages(self, material_id: UUID, page_nos: list[int]) -> dict[int, str]:
        """`material_pages.text` by `page_no`; pages with no row are left out."""
        ...


_TOPIC_COLUMNS = "id,exam_prep_id,name,order_index,importance,importance_reason,status,origin"


def _uuid(value: Any) -> UUID | None:
    return UUID(str(value)) if value is not None else None


def _time(value: Any) -> datetime | None:
    return datetime.fromisoformat(str(value)) if value is not None else None


def _topic(row: dict[str, Any]) -> TopicRow:
    importance = row.get("importance")
    return TopicRow(
        id=UUID(str(row["id"])),
        exam_prep_id=UUID(str(row["exam_prep_id"])),
        name=row["name"],
        order_index=int(row["order_index"]),
        importance=int(importance) if importance is not None else None,
        importance_reason=row.get("importance_reason"),
        status=row["status"],
        origin=row["origin"],
    )


class SupabaseScopeRepository:
    def __init__(self, connect: Callable[[], Client]) -> None:
        self._connect = connect
        self._client: Client | None = None
        # One request reads the files of a prep once (sources and questions both need them).
        self._files: dict[UUID, dict[str, dict[str, Any]]] = {}

    def _db(self) -> Client:
        if self._client is None:
            self._client = self._connect()
        return self._client

    def _run[T](self, what: str, query: Callable[[], T]) -> T:
        try:
            return query()
        except Exception as error:  # network, PostgREST, unexpected row shape
            raise unavailable(f"scope {what}", error) from error

    def get_prep(self, prep_id: UUID) -> ScopePrep | None:
        def query() -> ScopePrep | None:
            rows = (
                self._db()
                .table("exam_preps")
                .select("id,title,exam_date,active_scope_version_id")
                .eq("id", str(prep_id))
                .execute()
                .data
            )
            if not rows:
                return None
            row = rows[0]
            return ScopePrep(
                id=UUID(str(row["id"])),
                title=row["title"],
                exam_date=date.fromisoformat(str(row["exam_date"])),
                active_scope_version_id=_uuid(row.get("active_scope_version_id")),
            )

        return self._run("prep", query)

    def list_topics(self, prep_id: UUID) -> list[TopicRow]:
        def query() -> list[TopicRow]:
            rows = (
                self._db()
                .table("topics")
                .select(_TOPIC_COLUMNS)
                .eq("exam_prep_id", str(prep_id))
                .order("order_index")
                .execute()
                .data
            )
            return [_topic(r) for r in rows]

        return self._run("topics", query)

    def _materials(self, prep_id: UUID) -> dict[str, dict[str, Any]]:
        if prep_id not in self._files:
            rows = (
                self._db()
                .table("materials")
                .select("id,file_name,created_at")
                .eq("exam_prep_id", str(prep_id))
                .execute()
                .data
            )
            self._files[prep_id] = {str(r["id"]): r for r in rows}
        return self._files[prep_id]

    def list_sources(self, prep_id: UUID) -> list[SourceRange]:
        def query() -> list[SourceRange]:
            materials = self._materials(prep_id)
            if not materials:
                return []
            rows = (
                self._db()
                .table("topic_sources")
                .select("topic_id,material_id,page_from,page_to")
                .in_("material_id", list(materials))
                .execute()
                .data
            )
            return [
                SourceRange(
                    topic_id=UUID(str(r["topic_id"])),
                    material_id=UUID(str(r["material_id"])),
                    file_name=materials[str(r["material_id"])]["file_name"],
                    material_created_at=datetime.fromisoformat(
                        str(materials[str(r["material_id"])]["created_at"])
                    ),
                    page_from=int(r["page_from"]),
                    page_to=int(r["page_to"]),
                )
                for r in rows
            ]

        return self._run("sources", query)

    def list_questions(self, prep_id: UUID) -> list[QuestionRow]:
        def query() -> list[QuestionRow]:
            materials = self._materials(prep_id)
            if not materials:
                return []
            rows = (
                self._db()
                .table("past_exam_questions")
                .select("id,material_id,q_no,page_no,text,map_note,topic_id")
                .in_("material_id", list(materials))
                .execute()
                .data
            )
            return [
                QuestionRow(
                    id=UUID(str(r["id"])),
                    material_id=UUID(str(r["material_id"])),
                    file_name=materials[str(r["material_id"])]["file_name"],
                    material_created_at=datetime.fromisoformat(
                        str(materials[str(r["material_id"])]["created_at"])
                    ),
                    q_no=str(r["q_no"]),
                    page_no=int(r["page_no"]) if r.get("page_no") is not None else None,
                    text=r["text"],
                    map_note=r.get("map_note"),
                    topic_id=_uuid(r.get("topic_id")),
                )
                for r in rows
            ]

        return self._run("questions", query)

    def scope_version(self, version_id: UUID) -> VersionRow | None:
        def query() -> VersionRow | None:
            rows = (
                self._db()
                .table("scope_versions")
                .select("id,version,confirmed_at")
                .eq("id", str(version_id))
                .execute()
                .data
            )
            if not rows:
                return None
            row = rows[0]
            return VersionRow(UUID(str(row["id"])), int(row["version"]), _time(row["confirmed_at"]))

        return self._run("version", query)

    def has_changes_after(self, prep_id: UUID, after: datetime) -> bool:
        rows = self._run(
            "changes",
            lambda: (
                self._db()
                .table("scope_changes")
                .select("id")
                .eq("exam_prep_id", str(prep_id))
                .gt("created_at", after.isoformat())
                .limit(1)
                .execute()
                .data
            ),
        )
        return bool(rows)

    def latest_version(self, prep_id: UUID) -> int:
        rows = self._run(
            "latest version",
            lambda: (
                self._db()
                .table("scope_versions")
                .select("version")
                .eq("exam_prep_id", str(prep_id))
                .order("version", desc=True)
                .limit(1)
                .execute()
                .data
            ),
        )
        return int(rows[0]["version"]) if rows else 0

    def add_version(self, **fields: Any) -> UUID:
        row = {k: str(v) if isinstance(v, UUID) else v for k, v in fields.items()}
        if isinstance(row.get("confirmed_at"), datetime):
            row["confirmed_at"] = row["confirmed_at"].isoformat()
        try:
            rows = self._db().table("scope_versions").insert(row).execute().data
        except APIError as error:
            if error.code == _UNIQUE_VIOLATION:
                raise VersionTakenError(str(fields.get("version"))) from error
            raise unavailable("scope insert version", error) from error
        except Exception as error:
            raise unavailable("scope insert version", error) from error
        return self._run("inserted version", lambda: UUID(str(rows[0]["id"])))

    def set_active_version(self, prep_id: UUID, version_id: UUID) -> None:
        self._run(
            "set active version",
            lambda: (
                self._db()
                .table("exam_preps")
                .update({"active_scope_version_id": str(version_id)})
                .eq("id", str(prep_id))
                .execute()
            ),
        )

    def confirm_topics(self, prep_id: UUID) -> None:
        self._run(
            "confirm topics",
            lambda: (
                self._db()
                .table("topics")
                .update({"status": "confirmed"})
                .eq("exam_prep_id", str(prep_id))
                .eq("status", "draft")
                .execute()
            ),
        )

    def get_topic(self, topic_id: UUID) -> TopicRow | None:
        def query() -> TopicRow | None:
            rows = (
                self._db()
                .table("topics")
                .select(_TOPIC_COLUMNS)
                .eq("id", str(topic_id))
                .execute()
                .data
            )
            return _topic(rows[0]) if rows else None

        return self._run("topic", query)

    def pages(self, material_id: UUID, page_nos: list[int]) -> dict[int, str]:
        if not page_nos:
            return {}

        def query() -> dict[int, str]:
            rows = (
                self._db()
                .table("material_pages")
                .select("page_no,text")
                .eq("material_id", str(material_id))
                .in_("page_no", page_nos)
                .execute()
                .data
            )
            return {int(r["page_no"]): r["text"] for r in rows}

        return self._run("pages", query)


def get_scope_repository(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> ScopeRepository | None:
    """The repository for this user, or None without a user (the router keeps the stubs)."""
    if auth is None:
        return None
    return SupabaseScopeRepository(lambda: get_user_db(auth))
