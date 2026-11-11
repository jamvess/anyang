"""Exam preps in Supabase, read and written with the user's JWT so RLS decides what they see
(specs/features/exam-prep/create-exam-prep.md · apps/api/CLAUDE.md "Database").

The router depends on the `ExamPrepRepository` protocol through `get_exam_prep_repository`, so
unit tests swap in a fake. Any failure to reach or use the database becomes `DbUnavailableError`
(api.md v1.14 `503 db_unavailable`); details stay in the log.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Annotated, Any, Protocol
from uuid import UUID

import httpx
from fastapi import Depends
from postgrest.exceptions import APIError
from supabase import Client

from app.auth import AuthContext, get_auth, get_user_db
from app.domain.exam_prep import MaterialFacts

log = logging.getLogger(__name__)

# One query: the prep, plus the facts its stage needs (topics and files, also behind RLS).
_COLUMNS = (
    "id,title,exam_date,daily_minutes,created_at,active_scope_version_id,"
    "topics(importance),materials(kind_confirmed,status)"
)


class DbUnavailableError(Exception):
    """The database could not be reached or refused the query."""


@dataclass(frozen=True)
class ExamPrepRecord:
    id: UUID
    title: str
    exam_date: date
    daily_minutes: int | None
    created_at: datetime
    active_scope_version_id: UUID | None
    topic_importances: list[int | None] = field(default_factory=list)
    materials: list[MaterialFacts] = field(default_factory=list)


class ExamPrepRepository(Protocol):
    def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        title: str,
        exam_date: date,
        daily_minutes: int | None,
    ) -> ExamPrepRecord: ...

    def list_active(self) -> list[ExamPrepRecord]:
        """The user's preps with status 'active', in no particular order."""
        ...


def _record(row: dict[str, Any]) -> ExamPrepRecord:
    return ExamPrepRecord(
        id=UUID(row["id"]),
        title=row["title"],
        exam_date=date.fromisoformat(row["exam_date"]),
        daily_minutes=row["daily_minutes"],
        created_at=datetime.fromisoformat(row["created_at"]),
        active_scope_version_id=(
            UUID(row["active_scope_version_id"]) if row["active_scope_version_id"] else None
        ),
        topic_importances=[t["importance"] for t in row.get("topics") or []],
        materials=[
            MaterialFacts(kind_confirmed=m["kind_confirmed"], status=m["status"])
            for m in row.get("materials") or []
        ],
    )


class SupabaseExamPrepRepository:
    def __init__(self, client: Client) -> None:
        self._db = client

    def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        title: str,
        exam_date: date,
        daily_minutes: int | None,
    ) -> ExamPrepRecord:
        row = {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "title": title,
            "exam_date": exam_date.isoformat(),
            "daily_minutes": daily_minutes,
        }
        try:
            data = self._db.table("exam_preps").insert(row).execute().data
        except (httpx.HTTPError, APIError) as error:
            log.warning("exam_preps insert failed: %s: %s", type(error).__name__, error)
            raise DbUnavailableError from error
        # A new prep has no topics, files or scope yet.
        return _record(data[0])

    def list_active(self) -> list[ExamPrepRecord]:
        try:
            data = (
                self._db.table("exam_preps").select(_COLUMNS).eq("status", "active").execute().data
            )
        except (httpx.HTTPError, APIError) as error:
            log.warning("exam_preps select failed: %s: %s", type(error).__name__, error)
            raise DbUnavailableError from error
        return [_record(row) for row in data]


def get_exam_prep_repository(
    auth: Annotated[AuthContext | None, Depends(get_auth)],
) -> ExamPrepRepository | None:
    """The repository for this user, or None without a user (the router serves the stub)."""
    if auth is None:
        return None
    return SupabaseExamPrepRepository(get_user_db(auth))
