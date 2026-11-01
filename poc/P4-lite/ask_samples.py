"""PoC P4-lite: the tutor's replies to 3 real questions, to read next to the TTFT numbers.

    cd apps/api
    uv run python ../../poc/P4-lite/ask_samples.py http://127.0.0.1:8000 answers.json

A faster setting (less thinking) is only worth it if the replies stay right and still teach
without giving the answer away (ai-orchestration.md §2.2 teaching rules). A person reads them;
nothing is scored here. Results: poc/P4-lite/results/quality-low-vs-minimal.json.
"""

import json
import sys
from pathlib import Path

import httpx

QUESTIONS = [
    "ช่วยอธิบายว่าทำไม lim x→0 ของ sin x / x ถึงเท่ากับ 1 หน่อย",
    "หาอนุพันธ์ของ x^2 sin x ยังไงคะ ทำไม่เป็นเลย",
    "ผมได้ ∫ 2x dx = 2x^2 + C ถูกไหมครับ",
]
SESSION = "00000000-0000-4000-8000-000000000002"  # any id: sessions are stubs in P4-lite


def reply(client: httpx.Client, base: str, question: str) -> str:
    text, event = "", None
    url = f"{base}/sessions/{SESSION}/messages"
    with client.stream("POST", url, json={"text": question}) as response:
        for line in response.iter_lines():
            if line.startswith("event:"):
                event = line[len("event:") :].strip()
            elif line.startswith("data:") and event == "token":
                text += json.loads(line[len("data:") :].strip())["text"]
    return text


def main() -> None:
    base, out = sys.argv[1], Path(sys.argv[2])
    with httpx.Client(timeout=60) as client:
        answers = [{"q": q, "a": reply(client, base, q)} for q in QUESTIONS]
    out.write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
