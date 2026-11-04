"""api.md Endpoints: every endpoint in its tables is on /docs (D5 "ให้หน้า /docs ครบ").

The rows look like `| GET / PUT | `/me/tutor-profile` · `/me/buddy-profile` | … |`.
"""

import re
from pathlib import Path

from app.main import app

API_MD = Path(__file__).resolve().parents[4] / "specs" / "system" / "api.md"
ROW = re.compile(r"^\| ([A-Z]+(?: / [A-Z]+)*) \| (`.+?`) \|", re.MULTILINE)

# PUT {signed_url} goes from the browser straight to Supabase Storage.
NOT_OURS = {("put", "{signed_url}")}


def listed_endpoints() -> set[tuple[str, str]]:
    endpoints = set()
    for methods, paths in ROW.findall(API_MD.read_text(encoding="utf-8")):
        for method in methods.split(" / "):
            for path in re.findall(r"`([^`]+)`", paths):
                endpoints.add((method.lower(), path))
    return endpoints - NOT_OURS


def test_apimd_parses_the_endpoint_tables() -> None:
    """A row format that stops matching must not make the check below pass with nothing."""
    assert {("get", "/exam-preps"), ("put", "/me/profile"), ("delete", "/me")} <= listed_endpoints()


def test_apimd_every_endpoint_in_the_tables_is_in_openapi() -> None:
    paths = app.openapi()["paths"]

    missing = {
        (method, path) for method, path in listed_endpoints() if method not in paths.get(path, {})
    }

    assert missing == set()
