"""Press "ลองใหม่" on a failed file against a running API, as the browser would: find the failed
file of a prep, call POST /materials/{id}/retry, then poll until the file is classified, ready or
failed again (specs/features/exam-prep/material-retry.md · worklog feat-material-retry step 6).

A dev tool, like try_materials_flow.py: it talks to the API only (no service role), with the
token of an account you type in. Never use the demo account for tests (sprint-checklists D2 (ก)).

Usage, from apps/api, with the API running on this code (`uv run fastapi dev app/main.py`):
    uv run python -m scripts.try_material_retry ada9f476            # a prep id or its first chars
    uv run python -m scripts.try_material_retry ada9f476 --file sheet-04.pdf
"""

from __future__ import annotations

import argparse
import sys
import time

import httpx

from scripts.try_materials_flow import check, sign_in

DONE = {"classified", "ready", "failed"}  # where a retried file stops (spec §2.2 item 9)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("prep", help="the prep id, or its first characters")
    parser.add_argument("--file", help="the failed file's name (default: the only failed file)")
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--timeout", type=float, default=600, help="seconds to wait for the end")
    args = parser.parse_args()

    api = httpx.Client(base_url=args.api, timeout=60)
    api.headers["Authorization"] = f"Bearer {sign_in()}"

    preps = [p for p in check(api.get("/exam-preps"), 200) if p["id"].startswith(args.prep)]
    if len(preps) != 1:
        sys.exit(f"{len(preps)} preps of this account start with {args.prep!r}")
    prep_id = preps[0]["id"]
    print(f"prep {prep_id}")

    def materials() -> list[dict]:
        return check(api.get(f"/exam-preps/{prep_id}/materials"), 200)

    failed = [
        m for m in materials() if m["status"] == "failed" and args.file in (None, m["file_name"])
    ]
    if len(failed) != 1:
        sys.exit(f"{len(failed)} failed files match · pass --file <name>")
    file = failed[0]
    print(f"failed: {file['file_name']} · {file['error']}")

    started = time.monotonic()
    after = check(api.post(f"/materials/{file['id']}/retry"), 202)
    print(f"retry → 202 · status {after['status']} · error {after['error']}")

    last = None
    while True:
        row = next(m for m in materials() if m["id"] == file["id"])
        seen = (row["status"], row["kind"], row["kind_confidence"])
        if seen != last:
            print(f"  {time.monotonic() - started:4.0f} s  {row['status']}  {row['kind']}")
            last = seen
        if row["status"] in DONE:
            print(f"end: {row['status']} · kind {row['kind']} · {row['kind_confidence']}")
            print(f"     error {row['error']}")
            return
        if time.monotonic() - started > args.timeout:
            sys.exit(f"still {row['status']} after {args.timeout:.0f} s")
        time.sleep(3)


if __name__ == "__main__":
    main()
