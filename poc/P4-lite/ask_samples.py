"""PoC P4-lite: the tutor's replies to 3 real questions, to read next to the TTFT numbers.

    cd apps/api
    uv run python ../../poc/P4-lite/ask_samples.py http://127.0.0.1:8000 answers.json
    # an API with AUTH_REQUIRED=true: put a Supabase access token in ACCESS_TOKEN first

A faster setting (less thinking) is only worth it if the replies stay right and still teach
without giving the answer away (ai-orchestration.md §2.2 teaching rules). A person reads them;
nothing is scored here. Results: poc/P4-lite/results/quality-low-vs-minimal.json.
"""

import json
import os
import sys
from collections.abc import Iterable
from pathlib import Path

import httpx

QUESTIONS = [
    "ช่วยอธิบายว่าทำไม lim x→0 ของ sin x / x ถึงเท่ากับ 1 หน่อย",
    "หาอนุพันธ์ของ x^2 sin x ยังไงคะ ทำไม่เป็นเลย",
    "ผมได้ ∫ 2x dx = 2x^2 + C ถูกไหมครับ",
]
SESSION = "00000000-0000-4000-8000-000000000002"  # any id: sessions are stubs in P4-lite
NEWLINE = "\n"


def sse_events(lines: Iterable[str]) -> list[tuple[str, str]]:
    """(event name, data) per SSE block: a blank line ends a block, data lines are joined with
    newlines, and a block with no event field is "message" (as ttft.event_names)."""
    events: list[tuple[str, str]] = []
    name: str | None = None
    data: list[str] = []
    for raw in [*lines, ""]:
        line = raw.rstrip("\r\n")
        if line == "":
            if name is not None or data:
                events.append((name or "message", NEWLINE.join(data)))
            name, data = None, []
        elif line.startswith("event:"):
            name = line[len("event:") :].strip()
        elif line.startswith("data:"):
            data.append(line[len("data:") :].removeprefix(" "))
    return events


def reply(client: httpx.Client, base: str, question: str, token: str | None) -> str:
    """The tutor's text. An HTTP error or an `error` event raises, so a failed call never looks
    like an empty answer."""
    url = f"{base}/sessions/{SESSION}/messages"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    with client.stream("POST", url, json={"text": question}, headers=headers) as response:
        response.raise_for_status()
        events = sse_events(response.iter_lines())
    text = ""
    for name, data in events:
        if name == "error":
            raise RuntimeError(f"error event: {data}")
        if name == "token":
            text += json.loads(data)["text"]
    if not text:
        raise RuntimeError("the stream had no token text")
    return text


def main() -> None:
    base, out = sys.argv[1], Path(sys.argv[2])
    token = os.environ.get("ACCESS_TOKEN")  # for an API with AUTH_REQUIRED=true
    with httpx.Client(timeout=60) as client:
        answers = [{"q": q, "a": reply(client, base, q, token)} for q in QUESTIONS]
    out.write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
