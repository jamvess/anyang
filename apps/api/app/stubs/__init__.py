"""Fixture data for the tutor room and scope review stubs. Delete each file with the
stub endpoints that serve it.

Copied from apps/web/tests/fixtures/ (May's room, SSE and scope fixtures) because the
Docker image only contains apps/api/app/. Differences from the web copies:
`limits` comes from config/ai.yaml instead of the file, every message has `card`,
session_start.sse starts with a `session` event, and problem.purpose is `probe`
(the web copy's `check` is not a valid purpose). The scope files use uuid ids instead
of `t3` and so on; everything else matches (tests/unit/test_scope_stubs.py).
"""

import json
from functools import cache
from pathlib import Path
from typing import Any

_DIR = Path(__file__).parent


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
