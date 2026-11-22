"""Course files of an exam prep in Supabase, read and written with the user's JWT so RLS decides
what they see (specs/features/exam-prep/materials-db.md · apps/api/CLAUDE.md "Database").

The router depends on the `MaterialRepository` protocol through `get_material_repository`, so
unit tests swap in a fake. Any failure to reach or use the database becomes `DbUnavailableError`
(`503 db_unavailable`); details stay in the log.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any, Protocol
from uuid import UUID

from fastapi import Depends
from supabase import Client

from app.auth import get_optional_user_db
from app.db.errors import unavailable

_COLUMNS = (
    "id,tenant_id,exam_prep_id,storage_path,file_name,content_type,kind,kind_confidence,"
    "kind_confirmed,user_note,status,error,uploaded_at,created_at"
)


@dataclass(frozen=True)
class MaterialRecord:
    id: UUID
    tenant_id: UUID
    exam_prep_id: UUID
    storage_path: str
    file_name: str
    content_type: str | None  # null on rows made before 0008
    kind: str | None
    kind_confidence: float | None
    kind_confirmed: bool
    user_note: str | None
    status: str
    error: str | None
    uploaded_at: datetime | None  # null: the URL was given, /uploaded not called yet
    created_at: datetime


class MaterialRepository(Protocol):
    def prep_status(self, prep_id: UUID) -> str | None:
        """`exam_preps.status`, or None when the prep does not exist or RLS hides it."""
        ...

    def create(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        exam_prep_id: UUID,
        storage_path: str,
        file_name: str,
        content_type: str,
    ) -> MaterialRecord: ...

    def get(self, material_id: UUID) -> MaterialRecord | None: ...

    def mark_uploaded(self, material_id: UUID, *, user_note: str | None) -> MaterialRecord | None:
        """Set `uploaded_at` and the note, only while `uploaded_at` is null. None when no row
        changed (a second or a concurrent call)."""
        ...

    def list_for_prep(self, prep_id: UUID) -> list[MaterialRecord]:
        """Every row of the prep, in no particular order."""
        ...

    def confirm(self, material_id: UUID, *, kind: str) -> bool:
        """The user's kind, `kind_confirmed` and status `confirmed`, only while the status is
        `classified`. False when no row changed."""
        ...

    def retry(self, material_id: UUID, *, status: str) -> MaterialRecord | None:
        """Back to `status` with `error` null, only while the status is `failed` and
        `kind_confirmed` still matches it (`confirmed` ⇔ true · `retry_status`). None when no row
        changed (another request changed it first · material-retry.md §2.2 item 5)."""
        ...


def _time(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _record(row: dict[str, Any]) -> MaterialRecord:
    confidence = row["kind_confidence"]
    return MaterialRecord(
        id=UUID(row["id"]),
        tenant_id=UUID(row["tenant_id"]),
        exam_prep_id=UUID(row["exam_prep_id"]),
        storage_path=row["storage_path"],
        file_name=row["file_name"],
        content_type=row["content_type"],
        kind=row["kind"],
        kind_confidence=float(confidence) if confidence is not None else None,
        kind_confirmed=row["kind_confirmed"],
        user_note=row["user_note"],
        status=row["status"],
        error=row["error"],
        uploaded_at=_time(row["uploaded_at"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


class SupabaseMaterialRepository:
    def __init__(self, client: Client) -> None:
        self._db = client

    def prep_status(self, prep_id: UUID) -> str | None:
        try:
            data = (
                self._db.table("exam_preps").select("status").eq("id", str(prep_id)).execute().data
            )
        except Exception as error:
            raise unavailable("exam_preps select", error) from error
        return data[0]["status"] if data else None

    def create(
        self,
        *,
        id: UUID,
        tenant_id: UUID,
        exam_prep_id: UUID,
        storage_path: str,
        file_name: str,
        content_type: str,
    ) -> MaterialRecord:
        row = {
            "id": str(id),
            "tenant_id": str(tenant_id),
            "exam_prep_id": str(exam_prep_id),
            "storage_path": storage_path,
            "file_name": file_name,
            "content_type": content_type,
            "status": "uploaded",
        }
        try:
            return _record(self._db.table("materials").insert(row).execute().data[0])
        except Exception as error:
            raise unavailable("materials insert", error) from error

    def get(self, material_id: UUID) -> MaterialRecord | None:
        try:
            data = (
                self._db.table("materials")
                .select(_COLUMNS)
                .eq("id", str(material_id))
                .execute()
                .data
            )
            return _record(data[0]) if data else None
        except Exception as error:
            raise unavailable("materials select", error) from error

    def mark_uploaded(self, material_id: UUID, *, user_note: str | None) -> MaterialRecord | None:
        try:
            data = (
                self._db.table("materials")
                .update({"uploaded_at": datetime.now(UTC).isoformat(), "user_note": user_note})
                .eq("id", str(material_id))
                .is_("uploaded_at", "null")
                .execute()
                .data
            )
            return _record(data[0]) if data else None
        except Exception as error:
            raise unavailable("materials update uploaded_at", error) from error

    def list_for_prep(self, prep_id: UUID) -> list[MaterialRecord]:
        try:
            data = (
                self._db.table("materials")
                .select(_COLUMNS)
                .eq("exam_prep_id", str(prep_id))
                .execute()
                .data
            )
            return [_record(row) for row in data]
        except Exception as error:
            raise unavailable("materials select", error) from error

    def confirm(self, material_id: UUID, *, kind: str) -> bool:
        try:
            data = (
                self._db.table("materials")
                .update({"kind": kind, "kind_confirmed": True, "status": "confirmed"})
                .eq("id", str(material_id))
                .eq("status", "classified")
                .execute()
                .data
            )
            return bool(data)
        except Exception as error:
            raise unavailable("materials update confirm", error) from error

    def retry(self, material_id: UUID, *, status: str) -> MaterialRecord | None:
        try:
            data = (
                self._db.table("materials")
                .update({"status": status, "error": None})
                .eq("id", str(material_id))
                .eq("status", "failed")
                # the status was chosen from kind_confirmed: a row that moved on since the read
                # (retried, confirmed and failed again) is not sent back to the wrong step
                .eq("kind_confirmed", status == "confirmed")
                .execute()
                .data
            )
            return _record(data[0]) if data else None
        except Exception as error:
            raise unavailable("materials update retry", error) from error


def get_material_repository(
    db: Annotated[Client | None, Depends(get_optional_user_db)],
) -> MaterialRepository | None:
    """The repository for this user, or None without a user (the router serves the stub)."""
    return None if db is None else SupabaseMaterialRepository(db)
