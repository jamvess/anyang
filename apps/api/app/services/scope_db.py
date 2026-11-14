"""The scope page with a token (specs/features/scope/scope-db.md · api.md v1.6).

Plain functions the router runs in the thread pool (the Supabase client blocks). A refusal is a
`ScopeRefused` with the HTTP status and error code of api.md; the router turns it into the
error envelope before any write.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

from app.db.scope import QuestionRow, ScopeRepository, SourceRange, TopicRow, VersionTakenError
from app.domain.exam_prep import days_left
from app.domain.scope import (
    ScopeStatus,
    question_label,
    question_order,
    scope_status,
    source_label,
)
from app.models.scope import (
    PastQuestion,
    Scope,
    ScopeConfirmed,
    ScopeTopic,
    SourceExcerpt,
    TopicSources,
)

NOT_READY = "Topics or their stars are not ready yet"


@dataclass(frozen=True)
class ScopeRefused(Exception):
    status: int
    code: str
    message: str


def _not_found() -> ScopeRefused:
    return ScopeRefused(404, "not_found", "Not found")


def _ready_topics(repo: ScopeRepository, prep_id: UUID) -> list[TopicRow]:
    """§2.1 item 1: every topic has its stars, or the scope is not ready."""
    topics = repo.list_topics(prep_id)
    if not topics or any(t.importance is None for t in topics):
        raise ScopeRefused(409, "scope_not_ready", NOT_READY)
    return topics


def _stars(topic: TopicRow) -> int:
    return 0 if topic.status == "excluded" else topic.importance or 0


def _source_order(source: SourceRange) -> tuple[datetime, str, int, int]:
    return (source.material_created_at, str(source.material_id), source.page_from, source.page_to)


def _question_order(q: QuestionRow) -> tuple[datetime, str, int, tuple[int, int, str]]:
    return (q.material_created_at, str(q.material_id), q.page_no or 0, question_order(q.q_no))


def _past_question(q: QuestionRow) -> PastQuestion:
    return PastQuestion(
        id=q.id, label=question_label(q.file_name, q.q_no), text=q.text, map_note=q.map_note
    )


def _status(repo: ScopeRepository, prep_id: UUID, active: UUID | None) -> ScopeStatus:
    version = repo.scope_version(active) if active is not None else None
    confirmed_at = version.confirmed_at if version else None
    changed = confirmed_at is not None and repo.has_changes_after(prep_id, confirmed_at)
    return scope_status(active, confirmed_at, changed)


def scope_of(repo: ScopeRepository, prep_id: UUID, today: date) -> Scope:
    """§2.1: GET /exam-preps/{id}/scope."""
    prep = repo.get_prep(prep_id)
    if prep is None:
        raise _not_found()
    topics = _ready_topics(repo, prep_id)
    ranges: dict[UUID, list[SourceRange]] = {}
    for source in sorted(repo.list_sources(prep_id), key=_source_order):
        ranges.setdefault(source.topic_id, []).append(source)
    unmapped = sorted(
        (q for q in repo.list_questions(prep_id) if q.topic_id is None), key=_question_order
    )
    return Scope(
        prep_name=prep.title,
        days_left=days_left(prep.exam_date, today=today),
        status=_status(repo, prep_id, prep.active_scope_version_id),
        topics=[
            ScopeTopic(
                id=t.id,
                order=t.order_index,
                name=t.name,
                stars=_stars(t),
                reason=t.importance_reason or "",
                source_label=source_label(
                    [(s.file_name, s.page_from, s.page_to) for s in ranges.get(t.id, [])]
                ),
                origin=t.origin,  # type: ignore[arg-type]  # topics.origin check
            )
            for t in topics
        ],
        unmapped_questions=[_past_question(q) for q in unmapped],
    )


def sources_of(repo: ScopeRepository, topic_id: UUID) -> TopicSources:
    """§2.2: GET /topics/{id}/sources · each page once, by file then page."""
    topic = repo.get_topic(topic_id)
    # The prep too: topics follow the tenant (RLS `tenant_rows`), preps their user
    # (`owner_rows`), so a topic of another user of the tenant is not found (self-review).
    if topic is None or repo.get_prep(topic.exam_prep_id) is None:
        raise _not_found()
    mine = sorted(
        (s for s in repo.list_sources(topic.exam_prep_id) if s.topic_id == topic_id),
        key=_source_order,
    )
    excerpts: list[SourceExcerpt] = []
    if topic.origin != "user":
        files: dict[UUID, tuple[str, set[int]]] = {}
        for s in mine:
            files.setdefault(s.material_id, (s.file_name, set()))[1].update(
                range(s.page_from, s.page_to + 1)
            )
        for material_id, (name, pages) in files.items():
            ordered = sorted(pages)
            texts = repo.pages(material_id, ordered)
            excerpts += [
                SourceExcerpt(material_name=name, page=n, text=texts[n])
                for n in ordered
                if n in texts
            ]
    questions = sorted(
        (q for q in repo.list_questions(topic.exam_prep_id) if q.topic_id == topic_id),
        key=_question_order,
    )
    return TopicSources(excerpts=excerpts, questions=[_past_question(q) for q in questions])


def confirm(repo: ScopeRepository, prep_id: UUID, tenant_id: UUID, now: datetime) -> ScopeConfirmed:
    """§2.3: refusals first, then the version, the prep, the topics. ``now`` is the clock of
    the request (`get_now`), testable like the other endpoints."""
    prep = repo.get_prep(prep_id)
    if prep is None:
        raise _not_found()
    topics = _ready_topics(repo, prep_id)
    active = prep.active_scope_version_id
    if _status(repo, prep_id, active) == "confirmed":
        version_row = repo.scope_version(active) if active is not None else None
        if active is not None and version_row and any(t.status == "draft" for t in topics):
            # A confirm that failed after pointing the prep at its version: finish its topics
            # instead of refusing a retry for good (§2.3 item 5 · self-review PR #137).
            repo.confirm_topics(prep_id)
            return ScopeConfirmed(scope_version_id=active, version=version_row.version)
        raise ScopeRefused(409, "scope_already_confirmed", "The scope is already confirmed")
    if not any(t.status != "excluded" and (t.importance or 0) >= 1 for t in topics):
        raise ScopeRefused(409, "scope_empty", "Every topic is excluded")
    version = repo.latest_version(prep_id) + 1
    snapshot: list[dict[str, Any]] = [
        {
            "topic_id": str(t.id),
            "name": t.name,
            "order": t.order_index,
            "stars": _stars(t),
            "status": "confirmed" if t.status == "draft" else t.status,
            "origin": t.origin,
        }
        for t in topics
    ]
    try:
        version_id = repo.add_version(
            tenant_id=tenant_id,
            exam_prep_id=prep_id,
            version=version,
            status="confirmed",
            confirmed_at=now,
            snapshot=snapshot,
        )
    except VersionTakenError as error:  # another request confirmed first (§2.3 item 4)
        raise ScopeRefused(409, "scope_already_confirmed", "The scope is already confirmed") from (
            error
        )
    repo.set_active_version(prep_id, version_id)
    repo.confirm_topics(prep_id)
    return ScopeConfirmed(scope_version_id=version_id, version=version)
