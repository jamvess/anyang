"""Put the MTH10101 ingestion results into one exam prep, so it reaches the scope stage.

A dev tool for the demo (docs/worklog · scope-review.md §8): until the upload of demo step 3
(#140) works, this is how a prep gets real topics, stars, pages and past exam questions on
`anyang-dev`. It writes as the signed-in user (anon key + the user's token), so RLS keeps the rows
in that user's tenant. Never use the demo account for tests (sprint-checklists D2 (ก)).

Inputs (on Jam's machine; `poc/P3/out/` is not in git):
- `poc/P3/out/pages/<key>.json`      page text of each file
- `poc/P3/out/questions/<key>.json`  past exam questions of each exam file
- `poc/P3/results/apps-api-ingestion/topics.json` and `mapping.json` (PR #130)

Usage, from apps/api (SUPABASE_URL and SUPABASE_ANON_KEY of anyang-dev in .env):
    uv run python -m scripts.seed_scope_demo            # asks email + password, then the prep
    uv run python -m scripts.seed_scope_demo --prep <id>  # that prep
    uv run python -m scripts.seed_scope_demo --dry-run  # the row counts, no login
"""

from __future__ import annotations

import argparse
import getpass
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from supabase import create_client
from supabase_auth.errors import AuthApiError

from app.domain.ingestion import resolve_sources
from app.settings import get_settings

ROOT = Path(__file__).resolve().parents[3]
P3 = ROOT / "poc" / "P3"
PAGES = P3 / "out" / "pages"
QUESTIONS = P3 / "out" / "questions"
RESULTS = P3 / "results" / "apps-api-ingestion"

# Insert order: a row's parent goes first.
TABLES = ("materials", "material_pages", "topics", "topic_sources", "past_exam_questions")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows(tenant: str, prep: str) -> dict[str, list[dict[str, Any]]]:
    """Every row to insert, with fresh ids (pure: reads the P3 files, writes nothing)."""
    rows: dict[str, list[dict[str, Any]]] = {t: [] for t in TABLES}
    now = datetime.now(UTC).isoformat()
    keys: dict[str, str] = {}  # file key ("sheet-01") -> material id
    page_counts: dict[str, int] = {}
    for path in sorted(PAGES.glob("*.json")):
        key, doc = path.stem, _load(path)
        material = str(uuid.uuid4())
        keys[key] = material
        page_counts[material] = len(doc["pages"])
        exam = (QUESTIONS / path.name).exists()
        rows["materials"].append(
            {
                "id": material,
                "tenant_id": tenant,
                "exam_prep_id": prep,
                "storage_path": f"{tenant}/{prep}/{material}",
                "file_name": doc["file"],
                "kind": "past_exam" if exam else "sheet",
                "kind_confirmed": True,
                "status": "ready",
                "uploaded_at": now,  # GET /materials shows announced files only (0008)
            }
        )
        rows["material_pages"] += [
            {
                "tenant_id": tenant,
                "material_id": material,
                "page_no": page["page"],
                "text": page["text"],
                "extract_method": doc["method"],
            }
            for page in doc["pages"]
        ]

    topic_ids: dict[str, str] = {}
    for topic in _load(RESULTS / "topics.json"):
        topic_id = topic_ids[topic["id"]] = str(uuid.uuid4())
        rows["topics"].append(
            {
                "id": topic_id,
                "tenant_id": tenant,
                "exam_prep_id": prep,
                "name": topic["name"],
                "order_index": topic["order"],
                "importance": topic["stars"],
                "importance_reason": topic["reason"],
                "signal_r": topic["signal_r"],
                "status": "excluded" if topic["stars"] == 0 else "draft",
            }
        )
        rows["topic_sources"] += [
            {
                "tenant_id": tenant,
                "topic_id": topic_id,
                "material_id": r.material_id,
                "page_from": r.page_from,
                "page_to": r.page_to,
            }
            for r in resolve_sources(topic["sources"], keys, page_counts)
        ]

    mapping = _load(RESULTS / "mapping.json")
    for path in sorted(QUESTIONS.glob("*.json")):
        if path.stem not in keys:
            raise SystemExit(f"{path} has no page file {PAGES / path.name}")
        for q in _load(path)["questions"]:
            m = mapping.get(f"{path.stem}:{q['q_no']}") or {}
            rows["past_exam_questions"].append(
                {
                    "tenant_id": tenant,
                    "material_id": keys[path.stem],
                    "q_no": q["q_no"],
                    "page_no": q.get("page"),
                    "text": q["text"],
                    "topic_id": topic_ids.get(m.get("topic_id", "")),
                    "map_note": m.get("note") or None,
                }
            )
    return rows


def _counts(rows: dict[str, list[dict[str, Any]]]) -> str:
    return " · ".join(f"{t} {len(rows[t])}" for t in TABLES)


def _pick(preps: list[dict[str, Any]], wanted: str | None) -> dict[str, Any] | None:
    """The prep of `--prep`, or the one the user picks from a numbered list."""
    if wanted:
        return next((p for p in preps if p["id"] == wanted), None)
    for n, p in enumerate(preps, 1):
        print(f"{n}. {p['title']} · exam {p['exam_date']} · {p['id']}")
    choice = input("seed which prep (number): ").strip()
    return preps[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(preps) else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--prep", type=uuid.UUID, help="the exam prep id; without it, pick from a list"
    )
    parser.add_argument("--dry-run", action="store_true", help="print the row counts only")
    args = parser.parse_args()
    wanted = str(args.prep) if args.prep else None

    if args.dry_run:
        print("dry run:", _counts(build_rows(str(uuid.uuid4()), str(uuid.uuid4()))))
        return 0

    env = get_settings().env
    if not (env.supabase_url and env.supabase_anon_key.get_secret_value()):
        print("SUPABASE_URL / SUPABASE_ANON_KEY are not set in apps/api/.env", file=sys.stderr)
        return 1
    db = create_client(env.supabase_url, env.supabase_anon_key.get_secret_value())
    try:
        session = db.auth.sign_in_with_password(
            {
                "email": input("email (not the demo account): ").strip(),
                "password": getpass.getpass("password: "),
            }
        ).session
    except AuthApiError as error:
        session = None
        print(f"sign-in failed: {error.message}", file=sys.stderr)
    if session is None:
        return 1
    db.postgrest.auth(session.access_token)

    preps = (
        db.table("exam_preps")
        .select("id, tenant_id, title, exam_date")
        .order("created_at", desc=True)
        .execute()
        .data
    )
    found = _pick(preps, wanted)
    if found is None:
        print("no such exam prep in this account", file=sys.stderr)
        return 1
    prep = found["id"]
    if db.table("materials").select("id").eq("exam_prep_id", prep).limit(1).execute().data or (
        db.table("topics").select("id").eq("exam_prep_id", prep).limit(1).execute().data
    ):
        print("this prep has files or topics already: seed a new prep", file=sys.stderr)
        return 1

    rows = build_rows(found["tenant_id"], prep)
    try:
        for table in TABLES:
            for start in range(0, len(rows[table]), 200):
                db.table(table).insert(rows[table][start : start + 200]).execute()
    except Exception as error:
        # No transaction over PostgREST: remove what went in, so the prep can be seeded again.
        # Pages, sources and questions go with their file or topic (on delete cascade).
        db.table("topics").delete().eq("exam_prep_id", prep).execute()
        db.table("materials").delete().eq("exam_prep_id", prep).execute()
        print(f"seed failed, nothing kept ({type(error).__name__}: {error})", file=sys.stderr)
        return 1
    print(f"seeded '{found['title']}':", _counts(rows))
    print(f"open http://localhost:3000/preps/{prep}/scope (or the card on /)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
