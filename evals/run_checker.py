"""Run the answer checker over the golden set and write predictions for run_eval.py.

    uv run --project apps/api python evals/run_checker.py
    uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 \
        --predictions evals/answers/predictions/v1.jsonl

The checker is ``app.services.checker.check_answer`` (SymPy -> check_answer -> merge rules), with
the provider chosen by AI_PROVIDER: ``live`` calls Gemini with the key in .env, ``fake`` has no
scripted answers. Answers run one at a time (free tier request limits; the gateway retries rate
limits). An answer the gateway gives up on gets no prediction and is listed at the end;
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


async def run(
    rows: list[dict],
    *,
    out_path: Path,
    gateway: Gateway | None = None,
    pool: SympyWorkerPool | None = None,
) -> list[str]:
    """Check every row and write one prediction line per answer. Returns the skipped ids."""
    skipped: list[str] = []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as out:
        for row in rows:
            problem = CheckProblem(
                text=row["problem"],
                reference_answer=row["reference"],
                answer_format=row["answer_format"],
                solution_steps=[],  # the golden set has no course method (§10 decision 4)
            )
            try:
                result = await check_answer(
                    problem, row["lines"], gateway=gateway, pool=pool
                )
            except (AISchemaError, AIProviderError) as error:
                print(f"{row['id']}: skipped ({error})", file=sys.stderr)
                skipped.append(row["id"])
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
    return skipped


def main(argv: list[str] | None = None) -> int:
    version = get_settings().ai.purposes["check_answer"].prompt
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--out", type=Path, default=PREDICTIONS / f"{version}.jsonl")
    args = parser.parse_args(argv)

    rows = load_jsonl(args.labels)
    skipped = asyncio.run(run(rows, out_path=args.out))
    print(f"{len(rows) - len(skipped)}/{len(rows)} predictions -> {args.out}")
    if skipped:
        print(f"skipped: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
