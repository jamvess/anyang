"""Run the answer checker over the golden set and write predictions for run_eval.py.

    uv run --project apps/api python evals/run_checker.py
    uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 \
        --predictions evals/answers/predictions/v1.jsonl

The checker is ``app.services.checker.check_answer`` (SymPy -> check_answer -> merge rules), with
the provider chosen by AI_PROVIDER: ``live`` calls Gemini on Vertex AI when GOOGLE_CLOUD_PROJECT
is set (``--pause 1`` is enough there), ``fake`` has no scripted answers. Answers run one at a
time (the default pause fits the free tier of a Gemini API key; the gateway retries rate limits). An answer the gateway gives up on gets no prediction and is listed at the end;
run_eval.py counts it as a miss. Spec: specs/features/check/check-answer-classifier.md §2.6.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "apps" / "api"))

from app.ai.gateway import AIProviderError, AISchemaError, Gateway
from app.math.sympy_service import SympyWorkerPool
from app.services.checker import CheckProblem, check_answer
from app.settings import get_settings

LABELS = HERE / "answers" / "labels.jsonl"
PREDICTIONS = HERE / "answers" / "predictions"


def load_jsonl(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


# Free-tier Gemini allows 5 requests per minute per model (429 message of the first live run,
# 2026-10-28), so one answer every 13 s stays under it; a 429 that still happens waits a full
# minute. The gateway itself never waits that long (max_retry_wait_seconds, built for chat
# turns), so batch pacing lives here.
FREE_TIER_PAUSE_S = 13.0
RATE_LIMIT_WAIT_S = 60.0
RATE_LIMIT_RETRIES = 3


def _rate_limited(error: Exception) -> bool:
    return isinstance(error, AIProviderError) and "ProviderRateLimited" in str(error)


async def run(
    rows: list[dict],
    *,
    out_path: Path,
    gateway: Gateway | None = None,
    pool: SympyWorkerPool | None = None,
    append: bool = False,
    pause_s: float = 0.0,
    rate_limit_wait_s: float = RATE_LIMIT_WAIT_S,
    rate_limit_retries: int = 0,
) -> list[str]:
    """Check every row and write one prediction line per answer. Returns the skipped ids.

    ``pause_s`` spaces the answers out; a rate-limited answer is retried
    ``rate_limit_retries`` times after ``rate_limit_wait_s``. ``append`` keeps the lines
    already in ``out_path`` (``--resume``)."""
    skipped: list[str] = []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a" if append else "w", encoding="utf-8", newline="\n") as out:
        for i, row in enumerate(rows):
            if i and pause_s:
                await asyncio.sleep(pause_s)
            problem = CheckProblem(
                text=row["problem"],
                reference_answer=row["reference"],
                answer_format=row["answer_format"],
                solution_steps=[],  # the golden set has no course method (§10 decision 4)
            )
            for attempt in range(rate_limit_retries + 1):
                try:
                    result = await check_answer(
                        problem, row["lines"], gateway=gateway, pool=pool
                    )
                    break
                except (AISchemaError, AIProviderError) as error:
                    if _rate_limited(error) and attempt < rate_limit_retries:
                        print(
                            f"{row['id']}: rate limited, waiting {rate_limit_wait_s:.0f} s"
                        )
                        await asyncio.sleep(rate_limit_wait_s)
                        continue
                    print(f"{row['id']}: skipped ({error})", file=sys.stderr)
                    skipped.append(row["id"])
                    result = None
                    break
            if result is None:
                continue
            prediction = {
                "id": row["id"],
                "verdict": result.verdict,
                "error_type": result.error_type,
                "first_wrong_line": result.first_wrong_line,
                "evidence": result.evidence,
                "method": result.method,
                "decided_by": result.decided_by,
                "confidence": result.confidence,
                "disagreement": result.disagreement,
            }
            out.write(json.dumps(prediction, ensure_ascii=False) + "\n")
            out.flush()  # keep finished answers if the run stops (--resume)
    return skipped


def remaining_rows(rows: list[dict], out_path: Path) -> list[dict]:
    """The rows with no prediction in ``out_path`` yet (``--resume``)."""
    if not out_path.exists():
        return rows
    done = {prediction["id"] for prediction in load_jsonl(out_path)}
    return [row for row in rows if row["id"] not in done]


def main(argv: list[str] | None = None) -> int:
    version = get_settings().ai.purposes["check_answer"].prompt
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--out", type=Path, default=PREDICTIONS / f"{version}.jsonl")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="keep the predictions already in --out and check only the missing answers",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=FREE_TIER_PAUSE_S,
        help="seconds between answers (default fits the free tier; 0 for a paid key)",
    )
    args = parser.parse_args(argv)

    rows = load_jsonl(args.labels)
    if args.resume:
        total = len(rows)
        rows = remaining_rows(rows, args.out)
        print(
            f"resume: {total - len(rows)} already in {args.out}, {len(rows)} to check"
        )
    skipped = asyncio.run(
        run(
            rows,
            out_path=args.out,
            append=args.resume,
            pause_s=args.pause,
            rate_limit_retries=RATE_LIMIT_RETRIES,
        )
    )
    print(f"{len(rows) - len(skipped)}/{len(rows)} predictions -> {args.out}")
    if skipped:
        print(f"skipped: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
