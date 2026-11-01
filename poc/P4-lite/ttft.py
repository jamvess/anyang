"""PoC P4-lite: time to first token (TTFT) of the tutor room over SSE (NFR-P1).

Opens one session, then sends N messages one after another to
POST /sessions/{id}/messages and times each reply:

- ttft: request sent → first `token` event
- total: request sent → `done` event

Opening the session (`session_open`) and the first message (`first`) are kept
apart, because Cloud Run may have to start an instance (cold start).
Results go to results/<label>.json.

spec: specs/poc/README.md P4-lite · run from apps/api (see README.md).
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from collections.abc import Iterable, Iterator
from datetime import UTC, datetime
from pathlib import Path

import httpx

HERE = Path(__file__).parent
# Any id works on the stub; the same one the demo link uses (infra/README.md).
DEMO_PREP = "00000000-0000-4000-8000-000000000001"
SSE_HEADERS = {"Accept": "text/event-stream"}


def event_names(lines: Iterable[str]) -> Iterator[str]:
    """Names of the SSE events in a stream of lines.

    Uses the `event:` field; a block with data and no event is `message`.
    """
    name: str | None = None
    data = False
    for raw in lines:
        line = raw.rstrip("\r\n")
        if line == "":
            if name is not None or data:
                yield name or "message"
            name, data = None, False
        elif line.startswith("event:"):
            name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data = True
    if name is not None or data:
        yield name or "message"


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile (p in 0-100) of a non-empty list."""
    if not values:
        raise ValueError("no values")
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[rank - 1]


def summary(values: list[float]) -> dict[str, float]:
    return {
        "n": len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "min": min(values),
        "max": max(values),
        "mean": statistics.fmean(values),
    }


def timed_stream(client: httpx.Client, url: str, body: dict) -> dict[str, float | None]:
    """POST an SSE request; seconds to the first `token` and to `done` (None if not seen)."""
    start = time.perf_counter()
    ttft: float | None = None
    total: float | None = None

    def lines() -> Iterator[str]:
        with client.stream("POST", url, json=body, headers=SSE_HEADERS) as res:
            res.raise_for_status()
            yield from res.iter_lines()
            yield ""

    for name in event_names(lines()):
        now = time.perf_counter() - start
        if name == "token" and ttft is None:
            ttft = now
        if name == "done":
            total = now
            break
    return {"ttft": ttft, "total": total}


def open_session(client: httpx.Client, base: str, prep: str) -> str:
    """Start a session and return its id from the first `session` event."""
    with client.stream(
        "POST", f"{base}/exam-preps/{prep}/sessions", json={}, headers=SSE_HEADERS
    ) as res:
        res.raise_for_status()
        name = None
        for line in res.iter_lines():
            if line.startswith("event:"):
                name = line[len("event:") :].strip()
            elif line.startswith("data:") and name == "session":
                return json.loads(line[len("data:") :])["session_id"]
    raise RuntimeError("session stream did not send a `session` event")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--base", required=True, help="API base URL, e.g. the api-staging URL")
    parser.add_argument("--n", type=int, default=50, help="messages to send (default 50)")
    parser.add_argument("--prep", default=DEMO_PREP)
    parser.add_argument("--label", required=True, help="results file name, e.g. staging-fake")
    parser.add_argument("--pause", type=float, default=0.5, help="seconds between messages")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    with httpx.Client(timeout=60) as client:
        started = time.perf_counter()
        session = open_session(client, base, args.prep)
        # The first request after idle may include a Cloud Run cold start.
        session_open = time.perf_counter() - started
        runs = []
        for i in range(args.n):
            r = timed_stream(
                client, f"{base}/sessions/{session}/messages", {"text": f"P4-lite ttft {i + 1}"}
            )
            runs.append(r)
            print(f"{i + 1:>3}  ttft {r['ttft']:.3f}s  total {r['total']:.3f}s", flush=True)
            time.sleep(args.pause)

    ok = [r for r in runs if r["ttft"] is not None and r["total"] is not None]
    warm = ok[1:]
    result = {
        "label": args.label,
        "base": base,
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "messages": args.n,
        "failed": args.n - len(ok),
        "session_open": session_open,
        "first": ok[0] if ok else None,
        "ttft": summary([r["ttft"] for r in warm]) if warm else None,
        "total": summary([r["total"] for r in warm]) if warm else None,
        "runs": runs,
    }
    out = HERE / "results" / f"{args.label}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shown = ("session_open", "first", "ttft", "total", "failed")
    print(json.dumps({k: result[k] for k in shown}, indent=2))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
