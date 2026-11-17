"""Run demo step 3 end to end against a running API: create a prep, upload PDFs through signed
URLs, wait for the AI kinds, confirm them, wait for ingestion, then print the scope
(specs/features/exam-prep/materials-db.md · worklog feat-materials-storage step 7).

A dev tool, like seed_scope_demo.py. It talks to the API only (no service role), as the browser
would, with the token of an account you type in. Never use the demo account for tests
(sprint-checklists D2 (ก)). The files are not in git: download them from the MTH10101 Drive folder
(evals/topics/mth10101/sources.md) into evals/topics/mth10101/raw/ (gitignored). Never send the
held-out exam 2562/1.

Usage, from apps/api, with the API running (`uv run fastapi dev app/main.py`, AI_PROVIDER=live):
    uv run python -m scripts.try_materials_flow                 # every PDF in raw/
    uv run python -m scripts.try_materials_flow sheet-03.pdf midterm-2561-1.pdf
    uv run python -m scripts.try_materials_flow --api http://localhost:8000 --prep <id>
    uv run python -m scripts.try_materials_flow --title "MTH10101 กลางภาค"   # a fallback prep

The default title says it is a test. Pass --title for a prep that may appear on screen, such as
the fallback prep of the demo account (docs/design/demo-video.md).
"""

from __future__ import annotations

import argparse
import getpass
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import httpx
from supabase import create_client

from app.settings import get_settings

RAW = Path(__file__).resolve().parents[3] / "evals" / "topics" / "mth10101" / "raw"
HELD_OUT = "2562"
TEST_TITLE = "MTH10101 กลางภาค (ทดสอบอัปโหลด)"
NOTES = {"midterm-2559-1.pdf": "ข้อสอบกลางภาคปี 2559", "midterm-2561-1.pdf": "ข้อสอบกลางภาคปี 2561"}


def sign_in() -> str:
    env = get_settings().env
    email = input("email (test account, not the demo one): ").strip()
    password = getpass.getpass("password: ")
    client = create_client(env.supabase_url, env.supabase_anon_key.get_secret_value())
    session = client.auth.sign_in_with_password({"email": email, "password": password}).session
    return session.access_token


def check(response: httpx.Response, *expected: int) -> Any:
    if response.status_code not in expected:
        request = response.request
        sys.exit(f"{request.method} {request.url.path} → {response.status_code}: {response.text}")
    return response.json() if response.content else None


def wait(what: str, poll: Any, done: Any, timeout_s: float, every_s: float = 3) -> Any:
    start = time.monotonic()
    while True:
        value = poll()
        if done(value):
            print(f"  {what}: {time.monotonic() - start:.0f} s")
            return value
        if time.monotonic() - start > timeout_s:
            sys.exit(f"{what}: still not done after {timeout_s:.0f} s · last: {value}")
        time.sleep(every_s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", help="file names in raw/ (default: every PDF)")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--prep", help="use this prep instead of creating one")
    parser.add_argument("--title", default=TEST_TITLE, help="title of the prep it creates")
    args = parser.parse_args()

    paths = [RAW / f for f in args.files] if args.files else sorted(RAW.glob("*.pdf"))
    paths = [p for p in paths if HELD_OUT not in p.name]
    if not paths:
        sys.exit(f"no PDF in {RAW}")
    for path in paths:
        if not path.is_file():
            sys.exit(f"missing {path}")

    api = httpx.Client(base_url=args.api, timeout=60)
    api.headers["Authorization"] = f"Bearer {sign_in()}"

    prep_id = args.prep
    if prep_id is None:
        exam = date.today() + timedelta(days=14)
        body = {"title": args.title, "exam_date": exam.isoformat()}
        prep_id = check(api.post("/exam-preps", json=body), 201)["id"]
    print(f"prep {prep_id}")

    print("1. upload")
    for path in paths:
        data = path.read_bytes()
        ticket = check(
            api.post(
                f"/exam-preps/{prep_id}/materials",
                json={
                    "file_name": path.name,
                    "content_type": "application/pdf",
                    "size_bytes": len(data),
                },
            ),
            200,
        )
        put = httpx.put(
            ticket["upload_url"],
            content=data,
            headers={"Content-Type": "application/pdf"},
            timeout=300,
        )
        if put.status_code >= 300:
            sys.exit(f"PUT {path.name} → {put.status_code}: {put.text}")
        note = {"user_note": NOTES.get(path.name)}
        check(api.post(f"/materials/{ticket['material_id']}/uploaded", json=note), 202)
        print(f"  {path.name}: {len(data):,} bytes · {ticket['path']}")

    print("2. kinds (classify_material)")

    def materials() -> list[dict[str, Any]]:
        return check(api.get(f"/exam-preps/{prep_id}/materials"), 200)

    rows = wait(
        "classified",
        materials,
        lambda rows: all(r["status"] in ("classified", "failed") for r in rows),
        timeout_s=300,
    )
    for r in rows:
        kind = f"{r['kind']} ({r['kind_confidence']})"
        print(f"  {r['file_name']}: {r['status']} · {kind} {r['error'] or ''}")

    ready = [{"id": r["id"], "kind": r["kind"]} for r in rows if r["status"] == "classified"]
    print(f"3. confirm {len(ready)} files as the AI guessed")
    print(
        " ",
        check(api.post(f"/exam-preps/{prep_id}/materials/confirm", json={"materials": ready}), 202),
    )

    print("4. ingestion")

    def ingestion() -> dict[str, Any]:
        return check(api.get(f"/exam-preps/{prep_id}/ingestion"), 200)

    state = wait(
        "ingestion",
        ingestion,
        lambda s: s["scope_ready"] or any(step["status"] == "failed" for step in s["steps"]),
        timeout_s=1200,
        every_s=10,
    )
    for f in state["files"]:
        print(f"  {f['file_name']}: {f['status']} · {f['detail'] or ''} {f['error'] or ''}")
    for step in state["steps"]:
        print(f"  [{step['status']}] {step['label']}")
    if not state["scope_ready"]:
        sys.exit("ingestion failed")

    print("5. scope")
    scope = check(api.get(f"/exam-preps/{prep_id}/scope"), 200)
    for t in scope["topics"]:
        print(f"  {t['order']:>2}. {'★' * t['stars']:<3} {t['name']} · {t['source_label']}")
    print(f"  unmapped questions: {len(scope['unmapped_questions'])}")


if __name__ == "__main__":
    main()
