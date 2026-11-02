"""Fixture data for the tutor room, scope review and exam prep stubs. Delete each file with
the stub endpoints that serve it.

Copied from apps/web/tests/fixtures/ (May's room, SSE and scope fixtures) because the
Docker image only contains apps/api/app/. Differences from the web copies:
`limits` comes from config/ai.yaml instead of the file, every message has `card`,
session_start.sse starts with a `session` event, and problem.purpose is `probe`
(the web copy's `check` is not a valid purpose). The scope files use uuid ids instead
of `t3` and so on; everything else matches (tests/unit/test_scope_stubs.py).
These have no web copy: image_reply.sse and ocr_confirm.sse use the OCR3 example of
specs/features/check/ocr-confirm-card.md §3 and the verdict example of verdict-mark.md §3;
session_end.sse is the stub's own two-line summary; exam_preps.json and materials.json are
the stub's own too. exam_preps.json stores `days_left` and no `exam_date`, so the router
counts the date from today and the fixture never falls into the past.
"""

import json
from functools import cache
from pathlib import Path
from typing import Any

from fastapi.responses import JSONResponse

from app.auth import AuthContext
from app.models.error import error_response

_DIR = Path(__file__).parent

# Sent by every stub endpoint, so the web can tell fixture data from real data.
HEADERS = {"X-Stub": "true"}

# Stub URLs point here, never at real Storage.
STORAGE_URL = "https://stub.invalid/storage"

# Storage paths start with the tenant (data-model.md); anonymous requests (AUTH_REQUIRED=false)
# have none, so the stubs use a fixed one.
_TENANT = "00000000-0000-4000-8000-0000000000aa"


def tenant_of(auth: AuthContext | None) -> str:
    return str(auth.tenant_id) if auth else _TENANT


def error(status: int, code: str, message: str) -> JSONResponse:
    """The error envelope with X-Stub, so the web can tell stub errors from real ones too."""
    response = error_response(status, code, message)
    response.headers.update(HEADERS)
    return response


@cache
def room() -> dict[str, Any]:
    return json.loads((_DIR / "room.json").read_text(encoding="utf-8"))


@cache
def scope() -> dict[str, Any]:
    return json.loads((_DIR / "scope.json").read_text(encoding="utf-8"))


@cache
def topic_sources() -> dict[str, Any]:
    return json.loads((_DIR / "topic_sources.json").read_text(encoding="utf-8"))


@cache
def exam_preps() -> list[dict[str, Any]]:
    return json.loads((_DIR / "exam_preps.json").read_text(encoding="utf-8"))


@cache
def materials() -> list[dict[str, Any]]:
    return json.loads((_DIR / "materials.json").read_text(encoding="utf-8"))


@cache
def events(name: str) -> list[tuple[str, dict[str, Any]]]:
    """(event, data) pairs of a recorded SSE file. Comment lines are skipped."""
    pairs = []
    for block in (_DIR / f"{name}.sse").read_text(encoding="utf-8").split("\n\n"):
        event, data = "message", []
        for line in block.splitlines():
            field, _, value = line.partition(": ")
            if field == "event":
                event = value
            elif field == "data":
                data.append(value)
        if data:
            pairs.append((event, json.loads("\n".join(data))))
    return pairs
