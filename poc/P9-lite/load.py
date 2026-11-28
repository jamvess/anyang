"""PoC P9-lite · how far does the Gemini API free tier go (specs/poc/README.md P9-lite).

Runs tutor sessions through the real ``Gateway`` (prompts, config/ai.yaml, retries, SymPy) on
one AI Studio model and records every attempt the provider makes, because the gateway's own
retries hide 429 and 503 from ``ai_calls``. Inputs are synthetic only (``data/`` · AI-07).

Run from apps/api (GEMINI_API_KEY in the repo-root .env, key never printed):
    PYTHONUTF8=1 uv run python ../../poc/P9-lite/load.py --model gemini-3.5-flash-lite \
        --sessions 1 --label smoke-flash-lite
"""

from __future__ import annotations

import argparse
import asyncio
import contextvars
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from collections.abc import AsyncIterator
from contextlib import aclosing
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
API = HERE.parents[1] / "apps" / "api"
if str(API) not in sys.path:  # run as a script from apps/api: the app package is not on the path
    sys.path.insert(0, str(API))
DATA = HERE / "data"
RESULTS = HERE / "results"
SHEET = "synthetic-sheet-calculus.pdf"
TURNS = "student_turns.json"

# Thai topic names of the synthetic sheet and the pages they come from (make_sheet.PAGES).
TOPICS: list[tuple[str, list[int]]] = [
    ("ลิมิตของฟังก์ชัน", [1]),
    ("อนุพันธ์และกฎการหาอนุพันธ์", [2]),
    ("กฎลูกโซ่", [2, 3]),
]
NONE = "none"

_session: contextvars.ContextVar[int | None] = contextvars.ContextVar("p9_session", default=None)


def data_file(name: str) -> Path:
    """A file of ``data/`` and nothing else: the PoC never sends other files (AI-07)."""
    path = (DATA / name).resolve()
    if not path.is_relative_to(DATA):
        raise ValueError(f"P9-lite reads only synthetic files in {DATA}, not {name!r}")
    return path


_QUOTA_ID = re.compile(r"quotaId['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9_\-]+)")


_PROJECT = re.compile(r"projects/\d+")


def quota_id(message: str) -> str | None:
    """The ``quotaId`` a Gemini 429 names
    (``GenerateRequestsPerDayPerProjectPerModel-FreeTier`` is the daily one)."""
    found = _QUOTA_ID.search(message)
    return found.group(1) if found else None


def is_daily(quota: str | None) -> bool:
    return bool(quota) and "PerDay" in quota


@dataclass
class Attempt:
    """One request the provider made (or refused to make after the daily quota ran out)."""

    purpose: str
    kind: str  # generate | stream
    session: int | None
    at_s: float  # since the run started
    latency_s: float
    status: str  # ok | 429 | 503 | error | skipped_daily
    ttft_s: float | None = None
    code: int | None = None
    quota_id: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    message: str = ""


def _code(error: BaseException) -> int | None:
    from app.ai.providers.base import ProviderRateLimited

    if isinstance(error, ProviderRateLimited):
        return 429
    code = getattr(error, "code", None)
    return code if isinstance(code, int) else None


def _status(code: int | None) -> str:
    return {429: "429", 503: "503"}.get(code or 0, "error")


class CountingProvider:
    """Wraps the real provider. After a daily-quota 429 it stops sending: every later request
    is refused here with a wait no gateway table accepts, so the run ends without spending
    more attempts on a quota that is gone."""

    def __init__(self, inner: Any, clock=time.perf_counter) -> None:
        self._inner = inner
        self._clock = clock
        self._t0 = clock()
        self.attempts: list[Attempt] = []
        self.daily_exhausted = False

    def _record(self, request, kind: str, started: float, **fields: Any) -> None:
        self.attempts.append(
            Attempt(
                purpose=request.purpose,
                kind=kind,
                session=_session.get(),
                at_s=round(started - self._t0, 3),
                latency_s=round(self._clock() - started, 3),
                **fields,
            )
        )

    def _refuse_if_exhausted(self, request, kind: str) -> None:
        from app.ai.providers.base import ProviderRateLimited

        if self.daily_exhausted:
            self._record(request, kind, self._clock(), status="skipped_daily")
            raise ProviderRateLimited("P9-lite: daily quota used up, not sent", retry_after=1e9)

    def _failed(self, request, kind: str, started: float, error: BaseException, **extra) -> None:
        code = _code(error)
        # results/ is committed: a 429 names the project (projects/<number>), so it goes.
        message = _PROJECT.sub("projects/<n>", str(error))
        quota = quota_id(message)
        if code == 429 and is_daily(quota):
            self.daily_exhausted = True
        self._record(
            request,
            kind,
            started,
            status=_status(code),
            code=code,
            quota_id=quota,
            message=message[:400],
            **extra,
        )

    async def generate(self, request):
        self._refuse_if_exhausted(request, "generate")
        started = self._clock()
        try:
            response = await self._inner.generate(request)
        except Exception as error:
            self._failed(request, "generate", started, error)
            raise
        self._record(
            request,
            "generate",
            started,
            status="ok",
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
        )
        return response

    async def stream(self, request, usage) -> AsyncIterator[str]:
        self._refuse_if_exhausted(request, "stream")
        started = self._clock()
        ttft = None
        try:
            async with aclosing(self._inner.stream(request, usage)) as chunks:
                async for chunk in chunks:
                    if ttft is None:
                        ttft = round(self._clock() - started, 3)
                    yield chunk
        except Exception as error:
            self._failed(request, "stream", started, error, ttft_s=ttft)
            raise
        self._record(
            request,
            "stream",
            started,
            status="ok",
            ttft_s=ttft,
            tokens_in=usage.tokens_in,
            tokens_out=usage.tokens_out,
        )


@dataclass
class SessionOutcome:
    index: int
    completed: bool = False
    stopped: str = ""  # why the session ended early
    generate_tries: int = 0
    problems: int = 0  # problems that SymPy verified (AM-11)
    unverified: int = 0  # tries whose answer SymPy did not confirm
    errors: list[str] = field(default_factory=list)


class StopSession(Exception):
    """A 429 the gateway gave up on: the room would show "ระบบช้า", the session cannot go on."""


def sheet_pages() -> list[str]:
    from app.services.documents import PyMuPdfDocuments

    return PyMuPdfDocuments().pages_text(data_file(SHEET).read_bytes())


def load_turns() -> dict[str, Any]:
    return json.loads(data_file(TURNS).read_text(encoding="utf-8"))


async def _drain(gateway, purpose: str, values: dict[str, str]) -> str:
    parts: list[str] = []
    async with aclosing(gateway.stream(purpose, values)) as chunks:
        async for chunk in chunks:
            parts.append(chunk)
    return "".join(parts)


async def _guard(outcome: SessionOutcome, coro):
    """Run one step like the room does: a rate limit ends the session, any other AI failure
    is noted and the session goes on (the room degrades to a template)."""
    from app.ai.gateway import AIRateLimitedError

    try:
        return await coro
    except AIRateLimitedError as error:
        raise StopSession(str(error)) from error
    except Exception as error:  # schema, truncation, provider: the room carries on
        outcome.errors.append(f"{type(error).__name__}: {str(error)[:200]}")
        return None


async def _new_problem(gateway, settings, outcome, topic: str, source: str, previous: list[str]):
    from app.ai.gateway import AIRateLimitedError
    from app.models.tutor_ai import GenerateProblemResult
    from app.services.room_problems import ANSWER_FORMATS, verified

    values = {
        "topic": topic,
        "skills": NONE,
        "source_text": source,
        "difficulty": "2",
        "answer_formats": ANSWER_FORMATS,
        "previous_problems": "\n".join(f"- {p}" for p in previous) or NONE,
    }
    for _ in range(1 + settings.learning.checker.max_generate_retries):
        outcome.generate_tries += 1
        try:
            result = await gateway.call("generate_problem", values, GenerateProblemResult)
        except AIRateLimitedError as error:
            raise StopSession(str(error)) from error
        except Exception as error:
            outcome.errors.append(f"generate_problem {type(error).__name__}: {str(error)[:200]}")
            continue
        if await verified(result):
            outcome.problems += 1
            return result
        outcome.unverified += 1
    return None


async def _answer(gateway, outcome, problem, message: str, conversation: str) -> bool | None:
    """typed_answer → check_answer → explain_check, as the room does with a typed answer.
    True when the answer is right."""
    from app.models.check import TypedAnswer
    from app.services.checker import CheckProblem, check_answer, number_lines
    from app.services.photo_check import _check_result_text, _explain_input

    read = await _guard(
        outcome,
        gateway.call(
            "typed_answer",
            {"problem": problem.text, "conversation": conversation, "message": message},
            TypedAnswer,
        ),
    )
    if read is None or not read.is_answer or not read.lines:
        return None
    lines = list(read.lines)
    check_problem = CheckProblem(
        text=problem.text,
        reference_answer=problem.reference_answer,
        answer_format=problem.answer_format,
        solution_steps=list(problem.solution_steps),
    )
    result = await _guard(outcome, check_answer(check_problem, lines, gateway=gateway))
    if result is None:
        return None
    directive = "praise_and_show" if result.is_correct else "hint_1"
    values = _explain_input(
        check_problem, directive, number_lines(lines), _check_result_text(result)
    )
    await _guard(outcome, _drain(gateway, "explain_check", values))
    return result.is_correct


async def run_session(
    gateway, settings, index: int, pages: list[str], turns: dict, problems: int, chat: int
) -> SessionOutcome:
    """One tutor session on the synthetic sheet (spec P9-lite "ทำ")."""
    from app.models.tutor_ai import SessionSummaryResult

    _session.set(index)
    outcome = SessionOutcome(index=index)
    previous: dict[str, list[str]] = defaultdict(list)
    right = answers = 0
    try:
        for n in range(problems):
            topic, page_numbers = TOPICS[(index + n) % len(TOPICS)]
            source = "\n\n".join(pages[p - 1] for p in page_numbers)
            problem = await _new_problem(gateway, settings, outcome, topic, source, previous[topic])
            if problem is None:
                continue
            previous[topic].append(problem.text)
            if n == 0:
                facts = {
                    "days_left": "14",
                    "readiness": "0%",
                    "topics": "\n".join(name for name, _ in TOPICS),
                    "problem": problem.text,
                }
                await _guard(outcome, _drain(gateway, "open_session", facts))
            conversation = f"tutor: {problem.text}"
            tries = [problem.reference_answer]
            if n % 2 == 1:  # every second problem: wrong first, then right after the hint
                tries.insert(0, problem.reference_answer + turns["wrong_answer_suffix"])
            for message in tries:
                ok = await _answer(gateway, outcome, problem, message, conversation)
                answers += ok is not None
                right += bool(ok)
                conversation += f"\nstudent: {message}"
        for message in turns["chat"][:chat]:
            values = {"problem": NONE, "conversation": NONE, "message": message}
            await _guard(outcome, _drain(gateway, "tutor_reply", values))
        totals = {
            "prep_name": "แคลคูลัส 1 (ชุดสังเคราะห์)",
            "days_left": "14",
            "topics": NONE,
            "totals": f"ตอบ {answers} ครั้ง ถูก {right}",
        }
        await _guard(outcome, gateway.call("session_summary", totals, SessionSummaryResult))
        outcome.completed = True
    except StopSession as stop:
        outcome.stopped = str(stop)[:200]
    return outcome


async def run_classify(gateway, pages: list[str]) -> str:
    from app.domain.ingestion import pages_text
    from app.models.scope_ai import ClassifyMaterialResult

    _session.set(None)
    values = {
        "file_name": SHEET,
        "pages_text": pages_text(list(enumerate(pages, start=1))),
        "user_note": "ไม่มี",
    }
    try:
        result = await gateway.call("classify_material", values, ClassifyMaterialResult)
    except Exception as error:
        return f"{type(error).__name__}: {str(error)[:200]}"
    return f"{result.kind} {result.confidence}"


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, round(q * (len(ordered) - 1))))
    return ordered[rank]


def summarize(attempts: list[Attempt], calls: list[dict], sessions: list[SessionOutcome]) -> dict:
    by_status = Counter(a.status for a in attempts)
    sent = [a for a in attempts if a.status != "skipped_daily"]
    per_purpose: dict[str, dict] = {}
    for purpose in sorted({a.purpose for a in attempts}):
        mine = [a for a in sent if a.purpose == purpose]
        ok = [a for a in mine if a.status == "ok"]
        mine_calls = [c for c in calls if c["purpose"] == purpose]
        per_purpose[purpose] = {
            "attempts": len(mine),
            "ok": len(ok),
            "429": sum(a.status == "429" for a in mine),
            "503": sum(a.status == "503" for a in mine),
            "latency_p50_s": percentile([a.latency_s for a in ok], 0.5),
            "latency_p95_s": percentile([a.latency_s for a in ok], 0.95),
            "ttft_p95_s": percentile([a.ttft_s for a in ok if a.ttft_s is not None], 0.95),
            "tokens_in_max": max((a.tokens_in for a in ok), default=0),
            "schema_retries": sum(c["schema_retries"] for c in mine_calls),
            "call_status": dict(Counter(c["status"] for c in mine_calls)),
        }
    done = [s for s in sessions if s.completed]
    done_ids = {s.index for s in done}
    per_session = Counter(a.session for a in sent if a.session in done_ids)
    requests_per_session = sum(per_session.values()) / len(done) if done else None
    daily = [a for a in attempts if is_daily(a.quota_id)]
    tries = sum(s.generate_tries for s in sessions)
    return {
        "attempts_by_status": dict(by_status),
        "requests_sent": len(sent),
        "rate_429": round(by_status["429"] / len(sent), 3) if sent else None,
        "rate_503": round(by_status["503"] / len(sent), 3) if sent else None,
        "sessions_started": len(sessions),
        "sessions_completed": len(done),
        "requests_per_completed_session": requests_per_session,
        "ok_before_daily_quota": (
            sum(a.status == "ok" for a in attempts if a.at_s <= daily[0].at_s) if daily else None
        ),
        "daily_quota_id": daily[0].quota_id if daily else None,
        "generate_problem_verified_share": round(sum(s.problems for s in sessions) / tries, 3)
        if tries
        else None,
        "per_purpose": per_purpose,
    }


def build_gateway(settings, model: str, inner: Any) -> tuple[Any, CountingProvider]:
    """The real gateway with only the AI Studio provider: nothing can reach Vertex."""
    from app.ai.gateway import Gateway

    counter = CountingProvider(inner)
    gateway = Gateway.live(
        settings.ai, settings.env.prompts_dir, {"gemini": counter}, f"gemini:{model}"
    )
    return gateway, counter


async def run(args, settings, inner: Any) -> dict:
    gateway, counter = build_gateway(settings, args.model, inner)
    calls: list[dict] = []
    gateway.add_listener(lambda record: calls.append(asdict(record)))
    pages = sheet_pages()
    turns = load_turns()
    classify = await run_classify(gateway, pages) if args.classify else None

    sessions: list[SessionOutcome] = []
    started = 0
    while started < args.sessions and not counter.daily_exhausted:
        batch = range(started, min(started + args.concurrency, args.sessions))
        started = batch.stop
        sessions += await asyncio.gather(
            *(
                run_session(gateway, settings, i, pages, turns, args.problems, args.chat)
                for i in batch
            )
        )
        print(
            f"sessions {started}/{args.sessions} · requests {len(counter.attempts)} · "
            f"daily quota gone: {counter.daily_exhausted}",
            flush=True,
        )
    return {
        "meta": {
            "poc": "P9-lite",
            "label": args.label,
            "model": f"gemini:{args.model}",
            "ai_yaml_version": settings.ai.version,
            "started_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "args": vars(args),
            "classify": classify,
        },
        "summary": summarize(counter.attempts, calls, sessions),
        "sessions": [asdict(s) for s in sessions],
        "attempts": [asdict(a) for a in counter.attempts],
        "calls": calls,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--model", required=True, help="AI Studio model id, e.g. gemini-3.5-flash-lite"
    )
    parser.add_argument("--sessions", type=int, default=1, help="most sessions to start")
    parser.add_argument("--concurrency", type=int, default=1, help="sessions run at the same time")
    parser.add_argument("--problems", type=int, default=3, help="problems per session")
    parser.add_argument("--chat", type=int, default=2, help="free chat messages per session")
    parser.add_argument("--classify", action="store_true", help="also classify the synthetic sheet")
    parser.add_argument("--label", required=True, help="results/<label>.json")
    args = parser.parse_args()
    if ":" in args.model:
        parser.error("--model is the bare AI Studio id; the script adds 'gemini:'")

    # The script needs no Supabase: a .env with AUTH_REQUIRED=true must not stop it.
    os.environ["AUTH_REQUIRED"] = "false"
    from app.ai.providers.gemini import GeminiProvider
    from app.settings import get_settings

    if not data_file(SHEET).exists():
        print(
            "build the sheet first: uv run python ../../poc/P9-lite/make_sheet.py", file=sys.stderr
        )
        return 2
    settings = get_settings()
    key = settings.env.gemini_api_key.get_secret_value()
    if not key:
        print("GEMINI_API_KEY is empty in the repo-root .env", file=sys.stderr)
        return 2
    result = asyncio.run(run(args, settings, GeminiProvider(key)))
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"{args.label}.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
