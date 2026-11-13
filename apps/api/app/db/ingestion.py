"""Rows of ingestion (specs/features/scope/ingestion.md §2.1 to 2.6 · data-model.md รูป 2).

Two sides:
- the job writes with the service role and sets `tenant_id` on every row itself (spec §2.1
  item 4): `IngestionStore`, implemented by `SupabaseIngestionStore` and, for tests and local
  runs, `InMemoryIngestionStore`;
- `GET /exam-preps/{id}/ingestion` reads with the user's JWT so RLS decides:
  `IngestionReader`, from `get_ingestion_reader`.

The Supabase client is synchronous; the service calls the store from a worker thread. Any failure
to reach or use the database becomes `DbUnavailableError` (details in the log).
"""

import copy
import itertools
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from postgrest.types import CountMethod
from supabase import Client

from app.auth import AuthContext, get_auth, get_user_db
from app.db.errors import DbUnavailableError, unavailable

# Tables the job owns rows of, child first (what a re-run of one file clears · spec §2.3 item 6).
FILE_TABLES = ("material_pages", "chunks", "past_exam_questions")


@dataclass(frozen=True)
class MaterialRow:
    id: UUID
    tenant_id: UUID
    exam_prep_id: UUID
    file_name: str
    storage_path: str
    kind: str | None
    kind_confirmed: bool
    user_note: str | None
    relevance_weight: float
    status: str
    error: str | None
    created_at: datetime


def _material(row: dict[str, Any]) -> MaterialRow:
    return MaterialRow(
        id=UUID(str(row["id"])),
        tenant_id=UUID(str(row["tenant_id"])),
        exam_prep_id=UUID(str(row["exam_prep_id"])),
        file_name=row["file_name"],
        storage_path=row["storage_path"],
        kind=row.get("kind"),
        kind_confirmed=bool(row.get("kind_confirmed")),
        user_note=row.get("user_note"),
        relevance_weight=float(row["relevance_weight"]),
        status=row["status"],
        error=row.get("error"),
        created_at=_time(row.get("created_at")),
    )


def _time(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(UTC)


class IngestionStore(Protocol):
    """What the job reads and writes (service role). Every insert row carries `tenant_id`."""

    def prep_tenant(self, prep_id: UUID) -> UUID | None: ...
    def get_material(self, material_id: UUID) -> MaterialRow | None: ...
    def list_materials(self, prep_id: UUID) -> list[MaterialRow]:
        """Oldest first."""
        ...

    def update_material(self, material_id: UUID, fields: dict[str, Any]) -> None: ...
    def set_job(
        self,
        *,
        tenant_id: UUID,
        exam_prep_id: UUID,
        stage: str,
        status: str,
        material_id: UUID | None = None,
        error: str | None = None,
    ) -> None:
        """One row per (file or prep, stage): a new status replaces the old one."""
        ...

    def clear_file(self, material_id: UUID) -> None:
        """Delete the pages, chunks and questions of one file and its ingest job rows (not
        classify), so a re-run starts clean and an old failed stage does not show."""
        ...

    def upsert(self, table: str, rows: list[dict[str, Any]]) -> None:
        """Write whole rows by `id` in one call (rows that exist are replaced)."""
        ...

    def insert(self, table: str, rows: list[dict[str, Any]]) -> None: ...
    def select(self, table: str, **match: Any) -> list[dict[str, Any]]: ...
    def update(self, table: str, row_id: UUID, fields: dict[str, Any]) -> None: ...
    def delete_topics(self, topic_ids: Iterable[UUID]) -> None:
        """Delete topics; their skills and sources go with them (on delete cascade) and past
        exam questions keep no link to them (on delete set null)."""
        ...


# --- what GET /ingestion reads ---------------------------------------------------------------


@dataclass(frozen=True)
class FileSnapshot:
    material: MaterialRow
    jobs: list[tuple[str, str]]  # (stage, status)
    page_count: int
    question_count: int


@dataclass(frozen=True)
class IngestionSnapshot:
    files: list[FileSnapshot]  # confirmed files, oldest first
    prep_jobs: dict[str, str]  # stage → status of the prep's own steps (topics, stars)


class IngestionReader(Protocol):
    def snapshot(self, prep_id: UUID) -> IngestionSnapshot | None:
        """None when the prep does not exist or belongs to another tenant."""
        ...


# --- in memory ---------------------------------------------------------------------------------


@dataclass
class InMemoryIngestionStore:
    """The tables as lists of dicts, with the cascades of the schema. For tests and local runs.
    `reader_for(tenant_id)` sees only that tenant's rows, as RLS would."""

    tables: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    down: bool = False
    _fail_next: set[str] = field(default_factory=set)
    _clock: Iterable[int] = field(default_factory=itertools.count)

    def _table(self, name: str) -> list[dict[str, Any]]:
        return self.tables.setdefault(name, [])

    def _check(self) -> None:
        if self.down:
            raise DbUnavailableError("down")

    def _now(self) -> datetime:
        return datetime(2026, 11, 13, tzinfo=UTC) + timedelta(seconds=next(self._clock))  # type: ignore[call-overload]

    # seeding (tests) ---------------------------------------------------------------------------

    def add_prep(self, tenant_id: UUID) -> UUID:
        prep_id = uuid.uuid4()
        self._table("exam_preps").append({"id": prep_id, "tenant_id": tenant_id})
        return prep_id

    def add_material(
        self,
        prep_id: UUID,
        *,
        file_name: str,
        kind: str | None,
        storage_path: str,
        user_note: str | None = None,
        status: str = "confirmed",
        kind_confirmed: bool = True,
        relevance_weight: float = 1.0,
    ) -> UUID:
        material_id = uuid.uuid4()
        self._table("materials").append(
            {
                "id": material_id,
                "tenant_id": self.prep_tenant(prep_id),
                "exam_prep_id": prep_id,
                "file_name": file_name,
                "storage_path": storage_path,
                "kind": kind,
                "kind_confidence": None,
                "kind_confirmed": kind_confirmed,
                "user_note": user_note,
                "relevance_weight": relevance_weight,
                "status": status,
                "error": None,
                "created_at": self._now(),
            }
        )
        return material_id

    def add_topic(self, prep_id: UUID, *, name: str, origin: str) -> UUID:
        topic_id = uuid.uuid4()
        order = len([t for t in self._table("topics") if t["exam_prep_id"] == prep_id]) + 1
        self._table("topics").append(
            {
                "id": topic_id,
                "tenant_id": self.prep_tenant(prep_id),
                "exam_prep_id": prep_id,
                "name": name,
                "order_index": order,
                "prereq_ids": [],
                "importance": None,
                "importance_reason": None,
                "importance_source": "computed",
                "signal_r": None,
                "origin": origin,
                "status": "draft",
            }
        )
        return topic_id

    def add_job(
        self,
        prep_id: UUID,
        stage: str,
        status: str,
        *,
        material_id: UUID | None = None,
        error: str | None = None,
    ) -> None:
        self.set_job(
            tenant_id=self.prep_tenant(prep_id),  # type: ignore[arg-type]
            exam_prep_id=prep_id,
            stage=stage,
            status=status,
            material_id=material_id,
            error=error,
        )

    def add_pages(self, material_id: UUID, count: int) -> None:
        tenant = self._material_row(material_id)["tenant_id"]
        for n in range(1, count + 1):
            self._table("material_pages").append(
                {
                    "id": uuid.uuid4(),
                    "tenant_id": tenant,
                    "material_id": material_id,
                    "page_no": n,
                    "text": "",
                    "extract_method": "text_layer",
                }
            )

    def add_questions(self, material_id: UUID, count: int) -> None:
        tenant = self._material_row(material_id)["tenant_id"]
        for n in range(1, count + 1):
            self._table("past_exam_questions").append(
                {
                    "id": uuid.uuid4(),
                    "tenant_id": tenant,
                    "material_id": material_id,
                    "q_no": str(n),
                    "page_no": 1,
                    "text": "",
                    "topic_id": None,
                    "skill_id": None,
                    "trap": None,
                    "map_note": None,
                }
            )

    def set_error(self, material_id: UUID, text: str) -> None:
        self._material_row(material_id)["error"] = text

    def fail_writes_to(self, table: str) -> None:
        self._fail_next.add(table)

    def rows(self, table: str) -> list[dict[str, Any]]:
        return copy.deepcopy(self._table(table))

    def reader_for(self, tenant_id: UUID) -> "InMemoryIngestionReader":
        return InMemoryIngestionReader(self, tenant_id)

    # the store protocol ---------------------------------------------------------------------------

    def _material_row(self, material_id: UUID) -> dict[str, Any]:
        return next(m for m in self._table("materials") if m["id"] == material_id)

    def prep_tenant(self, prep_id: UUID) -> UUID | None:
        self._check()
        prep = next((p for p in self._table("exam_preps") if p["id"] == prep_id), None)
        return prep["tenant_id"] if prep else None

    def get_material(self, material_id: UUID) -> MaterialRow | None:
        self._check()
        row = next((m for m in self._table("materials") if m["id"] == material_id), None)
        return _material(row) if row else None

    def list_materials(self, prep_id: UUID) -> list[MaterialRow]:
        self._check()
        rows = [m for m in self._table("materials") if m["exam_prep_id"] == prep_id]
        return [_material(m) for m in sorted(rows, key=lambda m: m["created_at"])]

    def update_material(self, material_id: UUID, fields: dict[str, Any]) -> None:
        self._check()
        self._material_row(material_id).update(fields)

    def set_job(
        self,
        *,
        tenant_id: UUID,
        exam_prep_id: UUID,
        stage: str,
        status: str,
        material_id: UUID | None = None,
        error: str | None = None,
    ) -> None:
        self._check()
        jobs = self._table("ingestion_jobs")
        jobs[:] = [
            j
            for j in jobs
            if not (
                j["exam_prep_id"] == exam_prep_id
                and j["material_id"] == material_id
                and j["stage"] == stage
            )
        ]
        jobs.append(
            {
                "id": uuid.uuid4(),
                "tenant_id": tenant_id,
                "exam_prep_id": exam_prep_id,
                "material_id": material_id,
                "stage": stage,
                "status": status,
                "error": error,
                "updated_at": self._now(),
            }
        )

    def clear_file(self, material_id: UUID) -> None:
        self._check()
        for table in FILE_TABLES:
            rows = self._table(table)
            rows[:] = [r for r in rows if r["material_id"] != material_id]
        jobs = self._table("ingestion_jobs")
        jobs[:] = [j for j in jobs if j["material_id"] != material_id or j["stage"] == "classify"]

    def upsert(self, table: str, rows: list[dict[str, Any]]) -> None:
        self._check()
        if table in self._fail_next:
            self._fail_next.discard(table)
            raise DbUnavailableError(f"upsert {table}")
        for row in rows:
            next(r for r in self._table(table) if r["id"] == row["id"]).update(copy.deepcopy(row))

    def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        self._check()
        if table in self._fail_next:
            self._fail_next.discard(table)
            raise DbUnavailableError(f"insert {table}")
        for row in rows:
            self._table(table).append({"id": uuid.uuid4(), **copy.deepcopy(row)})

    def select(self, table: str, **match: Any) -> list[dict[str, Any]]:
        self._check()
        return [
            copy.deepcopy(r)
            for r in self._table(table)
            if all(r.get(k) == v for k, v in match.items())
        ]

    def update(self, table: str, row_id: UUID, fields: dict[str, Any]) -> None:
        self._check()
        if table in self._fail_next:
            self._fail_next.discard(table)
            raise DbUnavailableError(f"update {table}")
        next(r for r in self._table(table) if r["id"] == row_id).update(fields)

    def delete_topics(self, topic_ids: Iterable[UUID]) -> None:
        self._check()
        gone = set(topic_ids)
        skills = {s["id"] for s in self._table("topic_skills") if s["topic_id"] in gone}
        for table in ("topics",):
            self._table(table)[:] = [r for r in self._table(table) if r["id"] not in gone]
        for table in ("topic_skills", "topic_sources"):
            self._table(table)[:] = [r for r in self._table(table) if r["topic_id"] not in gone]
        for question in self._table("past_exam_questions"):
            if question.get("topic_id") in gone:
                question["topic_id"] = None
            if question.get("skill_id") in skills:
                question["skill_id"] = None


@dataclass
class InMemoryIngestionReader:
    store: InMemoryIngestionStore
    tenant_id: UUID

    def snapshot(self, prep_id: UUID) -> IngestionSnapshot | None:
        store = self.store
        store._check()
        if store.prep_tenant(prep_id) != self.tenant_id:
            return None
        files = []
        for material in store.list_materials(prep_id):
            if not material.kind_confirmed:
                continue
            jobs = [
                (j["stage"], j["status"])
                for j in store.select("ingestion_jobs", material_id=material.id)
            ]
            files.append(
                FileSnapshot(
                    material=material,
                    jobs=jobs,
                    page_count=len(store.select("material_pages", material_id=material.id)),
                    question_count=len(
                        store.select("past_exam_questions", material_id=material.id)
                    ),
                )
            )
        prep_jobs = {
            j["stage"]: j["status"]
            for j in store.select("ingestion_jobs", exam_prep_id=prep_id, material_id=None)
        }
        return IngestionSnapshot(files=files, prep_jobs=prep_jobs)


# --- Supabase ------------------------------------------------------------------------------------


def _json(value: Any) -> Any:
    """UUIDs and datetimes as strings for PostgREST."""
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json(v) for v in value]
    if isinstance(value, dict):
        return {k: _json(v) for k, v in value.items()}
    return value


def _ids(row: dict[str, Any]) -> dict[str, Any]:
    """Columns that hold ids back as UUID, as the in-memory store keeps them."""
    out = dict(row)
    for key in ("id", "tenant_id", "exam_prep_id", "material_id", "topic_id", "skill_id"):
        if out.get(key) is not None:
            out[key] = UUID(str(out[key]))
    if out.get("prereq_ids") is not None:
        out["prereq_ids"] = [UUID(str(v)) for v in out["prereq_ids"]]
    return out


class SupabaseIngestionStore:
    """The store with the service role (spec §2.1 item 4 · ingestion is a background job)."""

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
            raise unavailable(f"ingestion {what}", error) from error

    def prep_tenant(self, prep_id: UUID) -> UUID | None:
        rows = self._run(
            "prep",
            lambda: (
                self._db()
                .table("exam_preps")
                .select("tenant_id")
                .eq("id", str(prep_id))
                .execute()
                .data
            ),
        )
        return UUID(rows[0]["tenant_id"]) if rows else None

    def get_material(self, material_id: UUID) -> MaterialRow | None:
        rows = self._run(
            "material",
            lambda: (
                self._db().table("materials").select("*").eq("id", str(material_id)).execute().data
            ),
        )
        return _material(rows[0]) if rows else None

    def list_materials(self, prep_id: UUID) -> list[MaterialRow]:
        rows = self._run(
            "materials",
            lambda: (
                self._db()
                .table("materials")
                .select("*")
                .eq("exam_prep_id", str(prep_id))
                .order("created_at")
                .execute()
                .data
            ),
        )
        return [_material(r) for r in rows]

    def update_material(self, material_id: UUID, fields: dict[str, Any]) -> None:
        self.update("materials", material_id, fields)

    def set_job(
        self,
        *,
        tenant_id: UUID,
        exam_prep_id: UUID,
        stage: str,
        status: str,
        material_id: UUID | None = None,
        error: str | None = None,
    ) -> None:
        def query() -> None:
            jobs = self._db().table("ingestion_jobs")
            old = jobs.delete().eq("exam_prep_id", str(exam_prep_id)).eq("stage", stage)
            old = (
                old.eq("material_id", str(material_id))
                if material_id
                else old.is_("material_id", "null")
            )
            old.execute()
            jobs.insert(
                _json(
                    {
                        "tenant_id": tenant_id,
                        "exam_prep_id": exam_prep_id,
                        "material_id": material_id,
                        "stage": stage,
                        "status": status,
                        "error": error,
                        "updated_at": datetime.now(UTC),
                    }
                )
            ).execute()

        self._run("job", query)

    def clear_file(self, material_id: UUID) -> None:
        def query() -> None:
            for table in FILE_TABLES:
                self._db().table(table).delete().eq("material_id", str(material_id)).execute()
            (
                self._db()
                .table("ingestion_jobs")
                .delete()
                .eq("material_id", str(material_id))
                .neq("stage", "classify")
                .execute()
            )

        self._run("clear file", query)

    def upsert(self, table: str, rows: list[dict[str, Any]]) -> None:
        if rows:
            self._run(
                f"upsert {table}", lambda: self._db().table(table).upsert(_json(rows)).execute()
            )

    def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        if rows:
            self._run(
                f"insert {table}", lambda: self._db().table(table).insert(_json(rows)).execute()
            )

    def select(self, table: str, **match: Any) -> list[dict[str, Any]]:
        def query() -> list[dict[str, Any]]:
            q = self._db().table(table).select("*")
            for key, value in match.items():
                q = q.is_(key, "null") if value is None else q.eq(key, _json(value))
            return q.execute().data

        return [_ids(r) for r in self._run(f"select {table}", query)]

    def update(self, table: str, row_id: UUID, fields: dict[str, Any]) -> None:
        self._run(
            f"update {table}",
            lambda: self._db().table(table).update(_json(fields)).eq("id", str(row_id)).execute(),
        )

    def delete_topics(self, topic_ids: Iterable[UUID]) -> None:
        ids = [str(t) for t in topic_ids]
        if ids:
            self._run(
                "delete topics",
                lambda: self._db().table("topics").delete().in_("id", ids).execute(),
            )


class SupabaseIngestionReader:
    """Reads with the user's JWT: another tenant's prep is simply not there (RLS)."""

    def __init__(self, client: Client) -> None:
        self._db = client

    def snapshot(self, prep_id: UUID) -> IngestionSnapshot | None:
        def query() -> IngestionSnapshot | None:
            prep = self._db.table("exam_preps").select("id").eq("id", str(prep_id)).execute().data
            if not prep:
                return None
            materials = (
                self._db.table("materials")
                .select("*")
                .eq("exam_prep_id", str(prep_id))
                .eq("kind_confirmed", True)
                .order("created_at")
                .execute()
                .data
            )
            jobs = (
                self._db.table("ingestion_jobs")
                .select("material_id,stage,status")
                .eq("exam_prep_id", str(prep_id))
                .execute()
                .data
            )

            def count(table: str, material_id: str) -> int:
                # A count, not the rows: S11 polls, and PostgREST caps the rows it returns.
                result = (
                    self._db.table(table)
                    .select("id", count=CountMethod.exact, head=True)
                    .eq("material_id", material_id)
                    .execute()
                )
                return result.count or 0

            files = [
                FileSnapshot(
                    material=_material(m),
                    jobs=[(j["stage"], j["status"]) for j in jobs if j["material_id"] == m["id"]],
                    page_count=count("material_pages", m["id"]),
                    question_count=count("past_exam_questions", m["id"])
                    if m.get("kind") == "past_exam"
                    else 0,
                )
                for m in materials
            ]
            prep_jobs = {j["stage"]: j["status"] for j in jobs if j["material_id"] is None}
            return IngestionSnapshot(files=files, prep_jobs=prep_jobs)

        try:
            return query()
        except Exception as error:
            raise unavailable("ingestion snapshot", error) from error


def get_ingestion_reader(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> IngestionReader | None:
    """The reader for this user, or None without a user (the router serves the stub)."""
    if auth is None:
        return None
    return SupabaseIngestionReader(get_user_db(auth))


__all__ = [
    "DbUnavailableError",
    "FileSnapshot",
    "InMemoryIngestionStore",
    "IngestionReader",
    "IngestionSnapshot",
    "IngestionStore",
    "MaterialRow",
    "SupabaseIngestionReader",
    "SupabaseIngestionStore",
    "get_ingestion_reader",
]
